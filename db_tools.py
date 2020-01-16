from random import randint
from neo4j import GraphDatabase as GDB
from packages.cleaning.data_object import DataObj
from packages.cleaning import data_object_tools
class GDBCom():

    verbosity = True
    cache_commands = []
    graphDB_Driver = None


    def __init__(self,verbosity:bool=False):
        self.verbosity = verbosity

    def setup(self):
        uri             = "bolt://localhost:7687"
        user_name        = "neo4j"
        password        = "morphius4j"
        self.graphDB_Driver  = GDB.driver(uri, auth=(user_name, password))

    def print_progress(self, _msg):
        if self.verbosity: print(f'progress: {_msg}')

    def delete_all(self):
        self.cache_commands.append('match (x) detach delete x')





    def cache_execute(self, _single_transaction):
        with self.graphDB_Driver.session() as GDBS:

            if _single_transaction:
                cmd = ""
                for item in self.cache_commands:
                    cmd += f" {item} "
                GDBS.run(cmd)
                self.print_progress(f"executed: \n {cmd}")
            else:
                for cmd in self.cache_commands:
                    GDBS.run(cmd)
                    self.print_progress(f"executed: \n {cmd}")
                self.cache_commands.clear()
            GDBS.close()

    def execute_return(self, cmd):
        with self.graphDB_Driver.session() as GDBS:
            result: neo4j.BoltStatementResult = GDBS.run(cmd)
            return result.data()





    def create_tweet_node(self, alias:str, obj:DataObj, level:int, mode="queue"):
        siminet = data_object_tools.siminet_compressed_to_txt(obj.siminet_compressed)
        # // NOTE: setting siminet might have an issue: using single quotes
        # //        will lead to issues because of ' appears in the text due
        # //        to (i believe) the way a siminet is converted to text.
        # //        This should be fixed.
        command = f'''
            CREATE (alias{alias}:level_{level})
            SET alias{alias}.unique_id = '{obj.unique_id}'
            SET alias{alias}.name = '{obj.name}'
            SET alias{alias}.text = '{obj.text}'
            SET alias{alias}.siminet_compressed = "{siminet}"
        '''
        
        # // Be able to either send cmd to queue or return for further processing.
        valid_modes = ["queue", "return"]
        if mode not in valid_modes: 
            print_progress(f"Invalid mode: {mode}. Aborting.")
            return
        if mode == "queue":
            self.cache_commands.append(command)
        elif mode == "return":
            return command

    def convert_n4jdata_to_dataobjects(self, data):
        collection = []

        for d_dict in data:
            for key in d_dict:
                neo_node = d_dict[key]
                new_dataobj = self.convert_n4jnode_to_dataobj(neo_node, key)
                # // validate return and avoid duplicates. @@ Optimise.
                if new_dataobj:
                    unique_ids = [ c_obj.unique_id for c_obj in collection]
                    if new_dataobj.unique_id not in unique_ids:
                        collection.append(new_dataobj)
        return collection

    def convert_n4jnode_to_dataobj(self,neo_node, label:str) -> DataObj:
        
        if not neo_node:
            self.print_progress("Tried to convert n4jdata->dataobj:" 
                                "but encountered a NoneObj. Aborting.")
            return None

        unique_id = neo_node["unique_id"]
        name = neo_node["name"]
        text = neo_node["text"]
        siminet_compressed = neo_node["siminet_compressed"]
        siminet_compressed = data_object_tools.txt_to_compressed_siminet(siminet_compressed)

        new_dataobj = DataObj()
        new_dataobj.unique_id = unique_id
        new_dataobj.name = name
        new_dataobj.text = text
        new_dataobj.siminet_compressed = siminet_compressed
        return new_dataobj

    def get_dataobjects_from_node_by_pkeys(self, pkeys:list) -> list:
        #default_label = "node"
        collection = []

        for pk in pkeys:
            cmd = f"""
                MATCH (node)
                WHERE ID(node) = {pk}
                RETURN (node)
            """
            neo4j_data = self.execute_return(cmd)

            new_data_objects = self.convert_n4jdata_to_dataobjects(neo4j_data)
            #print(new_data_objects)
            collection.extend(new_data_objects)
        return collection





    def create_initial_ring(self, dataobjects: list) -> None:
        # // Note about connecting nodes:
        #   - Could be done by creating nodes here
        #   - Could be done by merging create string with connector string
        #   - Could be done by doing match. Might be slow though..

        cmd = ""
        id_last = None
        for i, obj in enumerate(dataobjects):
            cmd += self.create_tweet_node(str(i), obj, 0, "return")
            if id_last != None:
                cmd += f"\tCREATE (alias{id_last})-[con{i}:TICK]->(alias{i})"
            id_last = i
            cmd += "\n"

        # // connect last to first
        cmd += f"\tCREATE (alias{0})-[con{len(dataobjects)}:TIE]->(alias{id_last})"

        self.cache_commands.append(cmd)

    def get_ring_root(self):
        # // @@ Can be refactored by using get_ring_below
        cmd = """
            MATCH (strt:level_0)-[tie_r:TIE]->(last:level_0)
            MATCH (strt)-[tick_r:TICK*]-(connected)
            RETURN strt, connected
        """
        result = self.execute_return(cmd)
        return self.convert_n4jdata_to_dataobjects(result)

    def get_ring_from_obj(self, obj):
        # // wraps around, so if ring size is 3 and obj index is 1, 
        # // then the result is 1,2,0
        cmd = f"""
            MATCH (strt)
            WHERE strt.unique_id = '{obj.unique_id}'
            MATCH (strt)-[tick_r:TICK*]-(connected)
            RETURN strt, connected
        """
        # // return list of dataobjects
        neo4jdata = self.execute_return(cmd)
        return self.convert_n4jdata_to_dataobjects(neo4jdata)
 
    # // Not implemented
    def get_ring_below_node(self, connector_id):
        pass





    def get_level_from_node(self, obj):
        cmd = f"""
            MATCH (node)
            WHERE node.unique_id = '{obj.unique_id}'
            RETURN labels(node)
        """
        result = self.execute_return(cmd)
        #print(result[0])
        for key in result[0]:
            label = result[0][key][0] # // format: 'level_n'
            stripped = label.strip("level_")
            try:
                return int(stripped)
            except ValueError as e:
                self.print_progress("Tried to convert level label,",
                                    " but encountered an isse:\n",
                                    e)

    # // Not implemented @@
    def create_node_adjacent(self, obj_last, obj_new):
        pass

    def create_node_endof_ring(self, obj_ring:list, obj_new:DataObj):
        # // Get last object in ring
        if not obj_ring:
            self.print_progress("tried to create obj at the end of a ring " +
                                "but ring is empty. Aborting")
            return
        # // Identify last object, index doesn't matter because last node is autodetected
        # // from the ring it's on
        obj_last_in_ring = self.get_last_node_on_ring(obj_ring[0])[0]
        
        cmd = f"""
            MATCH (aliasnode_last)
            WHERE aliasnode_last.unique_id = '{obj_last_in_ring.unique_id}'
            MATCH (aliasnode_last)<-[oldTie:TIE]-(firstInRing)
        """
        # // Queue creation of new node
        target_level = self.get_level_from_node(obj_last_in_ring)
        cmd += self.create_tweet_node(alias="node_new", obj=obj_new, level=target_level, mode="return")
        # // Redo connections
        cmd += """\n
            CREATE (aliasnode_last)-[con:TICK]->(aliasnode_new)
            CREATE (aliasnode_new)<-[:TIE]-(firstInRing)
            DETACH DELETE oldTie
        """
        self.cache_commands.append(cmd)

    def get_last_node_on_ring(self, obj: DataObj):
        # // Hacky solution - returns last node if last node is not specified node
        cmd = f""" 
            MATCH (specifiedNode)
            WHERE specifiedNode.unique_id = '{obj.unique_id}'
            //MATCH (specifiedNode)-[:TICK*]-(pathNodes)-[:TIE]-(unknown)-[:TICK*]->(last)
            MATCH (specifiedNode)-[:TICK*]-(others)-[:TIE]-(some)
            MATCH (some)-[:TIE]->(target)
            RETURN target
        """
        neo4jdata = self.execute_return(cmd)
        objects = self.convert_n4jdata_to_dataobjects(neo4jdata)
        if not objects: # // Hacky.. @@ beware: check first if it's in db!
            objects.append(obj)
        return objects

    def create_node_below(self, obj_above, new_obj):
        cmd = f"""
            MATCH (node_above)
            WHERE node_above.unique_id = '{obj_above.unique_id}'

        """
        target_level = self.get_level_from_node(obj_above) + 1
        cmd += self.create_tweet_node(alias="node_below", obj=new_obj, level=target_level, mode="return")                          
        cmd += f"""
            CREATE (node_above)-[_:DOWN]->(aliasnode_below)
        """
        # // @@ Create ties?  EXPERIMENTAL: seems to be working.
        # // Added such that create_node_endof_ring & get_last_node_on_ring would work
        # // with below-nodes
        cmd += f"""
            CREATE (aliasnode_below)-[:TIE]->(aliasnode_below)
        """
        cmd += f"""
            CREATE (aliasnode_below)-[:TICK]->(aliasnode_below)
        """
        self.cache_commands.append(cmd)

    def get_node_below(self, obj, mode="dataobj"):
        cmd = f"""
            MATCH (node_above), (node_below)
            WHERE node_above.unique_id = '{obj.unique_id}'
            AND (node_above)-[:DOWN]->(node_below)
            RETURN node_below
        """
        result = self.execute_return(cmd)

        valid_modes = ["dataobj", "neo4jobj"]
        if mode not in valid_modes:
            print_progress(f"Invalid mode: {mode}. Aborting.")
            return 
        if mode == "dataobj":
            if result:
                return self.convert_n4jdata_to_dataobjects(result)
            else:
                return None
        elif mode == "neo4jobj":
            # // return a list of neo4j dict
            return result



    def assign_new_node(self, new_obj):
        pass
        # // probably recursive?
        
        # // high_node = Find node with highest score
        # // node_below = Get node below hight_node.
        # // Does it exist?
        # // No:
        # //    create node_below and return
        # // Yes: 
        # //     ring_size = get ring size of node_below
        # //     is ringsize > size limit?
        # //     No:
        # //        Attach new node at the end of current ring
        # //     Yes:
        # //        Do recursion with this ring



