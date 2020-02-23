from random import randint
from neo4j import GraphDatabase as GDB
from packages.cleaning.data_object import DataObj
from packages.cleaning import data_object_tools



class GDBCom():

    verbosity = True
    cache_commands = []
    graphDB_Driver = None


    def __init__(self, verbosity:bool = False):
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

    def delete_nodes(self, dataobjects:list)-> None:
        " Deletes all specified nodes. Executes immediately"
        if not dataobjects: return # // No point in doing anything if empty.
        cmd = ""
        for node in dataobjects:
            # // Note: cypher variables are enumerated like this because
            # // they need to be unique, and because using names can lead to isses.
            cmd += \
            f"""
                 MATCH (node{node.unique_id})
                 WHERE node{node.unique_id}.unique_id = '{node.unique_id}'
            """
        cmd += f"""
            DETACH DELETE {", ".join([f"node{node.unique_id}" for node in dataobjects])}
        """
        self.cache_commands.append(cmd)
        self.cache_execute(_single_transaction = False)        

    def cache_execute(self, _single_transaction):
        with self.graphDB_Driver.session() as GDBS:
            # @ Use try and clear cache in finally.
            if _single_transaction:
                cmd = ""
                for item in self.cache_commands:
                    cmd += f" {item} \n"
                GDBS.run(cmd)
                self.print_progress(f"executed: \n {cmd}")
            else:
                for cmd in self.cache_commands:
                    self.print_progress(f"executing: \n {cmd}")
                    GDBS.run(cmd)
                    self.print_progress("Cache execute completed.")
            self.cache_commands.clear()
            GDBS.close()

    def execute_return(self, cmd:str):
        with self.graphDB_Driver.session() as GDBS:
            result: neo4j.BoltStatementResult = GDBS.run(cmd)
            return result.data()



    def create_tweet_node(self, alias:str, obj:DataObj, level:int, mode="queue"):
        siminet_formatted = data_object_tools.siminet_compressed_to_txt(obj.siminet_compressed) # // @@ Should not be here 
        # // NOTE: setting siminet might have an issue: using single quotes
        # //        will lead to issues because of ' appears in the text due
        # //        to (i believe) the way a siminet is converted to text.
        # //        This should be fixed.
        command = f'''
            CREATE (alias{alias}:level_{level})
            SET alias{alias}.unique_id = '{obj.unique_id}'
            SET alias{alias}.name = "{obj.name}"
            SET alias{alias}.text = '{obj.text}'
            SET alias{alias}.siminet_compressed = "{siminet_formatted}"
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

    def convert_n4jdata_to_dataobjects(self, data) -> list:
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
        cmd += f"\tCREATE (alias{0})<-[con{len(dataobjects)}:UP]-(alias{id_last})"

        self.cache_commands.append(cmd)

    def get_ring_root(self):
        # // Getting the first ring
        cmd = """
            MATCH (strt:level_0)-[:TICK*]->(other:level_0)
            RETURN strt,other
        """
        result = self.execute_return(cmd)
        return self.convert_n4jdata_to_dataobjects(result)

    def get_ring_from_obj(self, obj):
        # // Gets ordered ring from any obj on that ring.
        last_obj_on_ring = self.get_last_node_on_ring(obj)[0]
        cmd = f"""
            MATCH (lastObj)
            WHERE lastObj.unique_id = '{last_obj_on_ring.unique_id}'
            MATCH (lastObj)<-[:TICK*]-(others)
            RETURN others
        """
        neo4jdata = self.execute_return(cmd)
        ring = self.convert_n4jdata_to_dataobjects(neo4jdata)
        ring.reverse()
        # // add last obj if it's not existing (must use ids)
        ids = [obj.unique_id for obj in ring]
        if last_obj_on_ring.unique_id not in ids: ring.append(last_obj_on_ring)
        return ring
 
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
        if not obj_ring:
            self.print_progress("tried to create obj at the end of a ring " +
                                "but ring is empty. Aborting")
            return
        # // Index doesn't matter because last node is autodetected
        anyobj_in_ring = obj_ring[0]
        obj_last_in_ring = self.get_last_node_on_ring(anyobj_in_ring)[0]
        
        cmd = f"""
            MATCH (aliasnode_last)
            WHERE aliasnode_last.unique_id = '{obj_last_in_ring.unique_id}'
            MATCH (aliasnode_last)-[oldUpTie:UP]->(firstInRing)
            //MATCH (aliasnode_last)-[oldSelfTick:TICK]->(aliasnode_last)
        """
        if len(obj_ring) == 1: # // remove self tick from first DOWN insert
            cmd += """
                MATCH (aliasnode_last)-[oldSelfTick:TICK]->(aliasnode_last)
                DETACH DELETE oldSelfTick
            """
        # // Queue creation of new node
        target_level = self.get_level_from_node(obj_last_in_ring)
        cmd += self.create_tweet_node(alias="node_new", obj=obj_new, level=target_level, mode="return")
        # // Redo connections
        cmd += """\n
            CREATE (aliasnode_last)-[:TICK]->(aliasnode_new)
            CREATE (aliasnode_new)-[:UP]->(firstInRing)
            DETACH DELETE oldUpTie//, oldSelfTick
        """ # // TODO: The '//' is above line, why is it there, typo?
        self.cache_commands.append(cmd)

    def get_last_node_on_ring(self, obj: DataObj):
        # TODO: accept obj arg as list?
        cmd = f""" 
            MATCH (specifiedNode)
            WHERE specifiedNode.unique_id = '{obj.unique_id}'
            MATCH (specifiedNode)-[:TICK*]->(last)
            WHERE (last)-[:UP]->()
            RETURN last
        """
        neo4jdata = self.execute_return(cmd)
        objects = self.convert_n4jdata_to_dataobjects(neo4jdata)
        if not objects: # // If no objects, the obj arg is last.
            objects.append(obj)
        return objects

    def create_node_below(self, obj_above, new_obj):
        cmd = f"""
            MATCH (node_above)
            WHERE node_above.unique_id = '{obj_above.unique_id}'
        """
        target_level = self.get_level_from_node(obj_above) + 1
        cmd += self.create_tweet_node(alias="node_below", obj=new_obj, level=target_level, mode="return") 
        # // Create ties:                         
        cmd += f"""
            CREATE (node_above)-[:DOWN]->(aliasnode_below)
            CREATE (aliasnode_below)-[:UP]->(node_above)
            CREATE (aliasnode_below)-[:TICK]->(aliasnode_below)
        """
        self.cache_commands.append(cmd)

    def get_descendants(self, dataobj) -> list:
        """ Get all descendants of a certain node.
        """
        def bungee(dataobj):
            total = []
            node_below = self.get_node_below(dataobj)

            if node_below:
                node_below = node_below[0]
                below_ring = self.get_ring_from_obj(obj=node_below)

                for node in below_ring:
                    total.append(node)
                    total.extend(bungee(node))
            return total

        return bungee(dataobj)

    def get_connectors_of(self, obj):

        cmd = f"""
            MATCH (org), (other)
            WHERE org.unique_id = '{obj.unique_id}'
            MATCH (org)-[connector]-(other)
            RETURN other, connector, startNode(connector) as startRef
        """
        result = self.execute_return(cmd=cmd)
        # // TEST: show all connectors and such
        # print(obj.name)
        # for i, d_dict in enumerate(result):
        #     print() # // space for visualisation
        #     for key in d_dict:
        #         print() # // space for visualisation
        #         print(f"{i}: {key}")
        #         if key == "startRef":
        #             print(d_dict.get(key).id)
        #         if key == "connector":
        #             print("-Connector properties-:")
        #             #print(d_dict.get(key))
        #             print(d_dict.get(key).id)
        #             print(d_dict.get(key).type)
        #         if key == "other":
        #             print("-node properties-:")
        #             #print(d_dict.get(key))
        #             print(d_dict.get(key).id)
        #             print(d_dict.get(key).get("name"))
        #             print(d_dict.get(key).get("unique_id"))
        return result

    def swap_nodes(self, objs_old:list, objs_new:list) -> None: # // lists of dataobj

            cmd = ""
            # // Enumerate old objects for identification later on.
            for i, obj in enumerate(objs_old):
                cmd += f"MATCH (objOld{i}) WHERE objOld{i}.unique_id = '{obj.unique_id}'"

            # // Do swaps.
            for i in range(len(objs_old)):
                # // Format siminets such that the database can contain them.
                siminet_formatted = data_object_tools.siminet_compressed_to_txt(
                                        objs_new[i].siminet_compressed
                                    )
                self.print_progress( # // Status update
                    f"Que swap: '{objs_new[i].name}' -> node({objs_old[i].name})"
                )
                cmd += f"""
                    SET objOld{i}.unique_id = '{objs_new[i].unique_id}'
                    SET objOld{i}.name = "{objs_new[i].name}"
                    SET objOld{i}.text = '{objs_new[i].text}'
                    SET objOld{i}.siminet_compressed = "{siminet_formatted}"
                """
            # @ Auto-execute; might use this as an option.
            self.cache_commands.append(cmd)
            self.cache_execute(False)


    def get_node_next(self, obj, rel_type: str) -> list:
        """ Gets the next node from a specific node, based on relation type
            Supported reltypes are:
                'TICK', 'UP', 'DOWN'
        """
        if rel_type not in ["TICK", "UP", "DOWN"]: # // supported moves
            self.print_progress(f"get_node_next: rel_type '{rel_type}' not supported.")
            return []
        cmd = f"""
            MATCH (node_current), (node_next)
            WHERE node_current.unique_id = '{obj.unique_id}'
            AND (node_current)-[:{rel_type}]->(node_next)
            RETURN node_next
        """
        result = self.execute_return(cmd)
        return self.convert_n4jdata_to_dataobjects(result)

    def get_node_below(self, obj) -> list:
        """ Returns a list containing nodes which are connected to 
            the dataobj given as an argument, with the relationship
            named 'DOWN'.
        """
        return self.get_node_next(obj=obj, rel_type="DOWN")
        
    def get_node_tick(self, obj) -> list:
        """ Returns a list containing nodes which are connected to 
            the dataobj given as an argument, with the relationship
            named 'TICK'.
        """
        return self.get_node_next(obj=obj, rel_type="TICK")

    def get_node_above(self, obj) -> list:
        """ Returns a list containing nodes which are connected to 
            the dataobj given as an argument, with the relationship
            named 'UP'.
        """
        return self.get_node_next(obj=obj, rel_type="UP")

    def check_if_last(self, obj) -> bool:
        " Checks if an object is the last in the db structure."
        root_ring_unsorted = self.get_ring_root()
        if root_ring_unsorted:
            root_ring_sorted = self.get_ring_from_obj(root_ring_unsorted[0])
            if root_ring_sorted:
                if obj.unique_id == root_ring_sorted[-1].unique_id:
                    return True
        return False
        



