from random import randint
from neo4j import GraphDatabase as GDB
from packages.cleaning.data_object import DataObj
from packages.cleaning import data_object_tools
from credentials import neo4j_uri, neo4j_user_name, neo4j_password



class GDBCom():

    verbosity = True
    cache_commands = []
    graphDB_Driver = None


    def __init__(self, verbosity:bool = False):
        self.verbosity = verbosity


    def setup(self) -> None:
        "Sets up credentials and DB Driver"
        uri = neo4j_uri
        user_name = neo4j_user_name
        password = neo4j_password
        self.graphDB_Driver  = GDB.driver(uri, auth=(user_name, password))


    def print_progress(self, _msg) -> None:
        """ All print statements will go through here and print 
            only if self.verbosity is True.
        """
        if self.verbosity: print(f'progress: {_msg}')


    def delete_all(self) -> None:
        "Snippet for deleting everything in the database"
        self.cache_commands.append('match (x) detach delete x')


    def delete_nodes(self, dataobjects:list)-> None:
        " Deletes all specified nodes. Executes immediately "
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


    def cache_execute(self, _single_transaction:bool) -> None:
        """ Executes everything in the self.cache_commands,
            either in one single transaction, or one command
            snippet at a time.

            NOTE: This method only supports _single_transaction=True
                    -AA 050320
        """
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


    def execute_return(self, cmd:str): # -> Neo4j data. See documentation for details.
        "Runs a command to the Neo4j DB and returns result."
        with self.graphDB_Driver.session() as GDBS:
            result: neo4j.BoltStatementResult = GDBS.run(cmd)
            return result.data()


    def create_tweet_node(self, alias:str, obj:DataObj, level:int, mode="queue"): # -> str or None
        """ Converts a dataobject(packages.cleaning.data_object) into a 
            neo4j formatted command (string).

            Can either return that command or send it to self.cache_commands.
            Valid modes = "queued" and "return". Incorrect mode will raise 
            ValueError.
        """
        # // Format siminet(see packages.similarity.process_tools), which
        # // is a 2d list into a string which can be stored in the neo4j DB
        siminet_formatted = data_object_tools.siminet_to_txt(obj.siminet) 
        # // Formatted command.
        command = f'''
            CREATE (alias{alias}:level_{level})
            SET alias{alias}.unique_id = '{obj.unique_id}'
            SET alias{alias}.name = "{obj.name}"
            SET alias{alias}.text = '{obj.text}'
            SET alias{alias}.siminet = "{siminet_formatted}"
        '''
        # // Be able to either send cmd to queue or return for further processing.
        valid_modes = ["queue", "return"]
        if mode not in valid_modes:
            raise ValueError("mode not recognised.")
        if mode == "queue":
            self.cache_commands.append(command)
        elif mode == "return":
            return command


    def convert_n4jdata_to_dataobjects(self, data) -> list: # // Input data is Neo4j data.
        """ Gets data from neo4j (see neo4j documentation for more details)
            and converts it to dataobjects(list) if it is possible.
        """
        collection = []

        for d_dict in data: # // Data should contain dicts.
            for key in d_dict:
                neo_node = d_dict[key] # // Allow crash.
                new_dataobj = self.convert_n4jnode_to_dataobj(neo_node, key)
                # // validate return and avoid duplicates.
                if new_dataobj:
                    # // Ensure no duplicates.
                    unique_ids = [c_obj.unique_id for c_obj in collection]
                    if new_dataobj.unique_id not in unique_ids:
                        collection.append(new_dataobj)
        return collection # // Return list of dataobjects.


    def convert_n4jnode_to_dataobj(self, neo_node, label:str) -> DataObj:
        """ Takes neo4j data, formats it into a 
            DataObj(packages.cleaning.data_object)
            and returns it.
        """
        if not neo_node:
            self.print_progress("Tried to convert n4jdata->dataobj:" 
                                "but encountered a NoneObj. Aborting.")
            return None

        unique_id = neo_node["unique_id"]
        name = neo_node["name"]
        text = neo_node["text"]
        siminet = neo_node["siminet"]
        siminet = data_object_tools.txt_to_siminet(siminet)

        new_dataobj = DataObj()
        new_dataobj.unique_id = unique_id
        new_dataobj.name = name
        new_dataobj.text = text
        new_dataobj.siminet = siminet
        return new_dataobj


    def get_dataobjects_from_node_by_pkeys(self, pkeys:list) -> list:
        """ Get dataobject(packages.cleaning.data_object) form
            Neo4j database by pkeys, which refers to the unique
            keys assigned in the db. This is not the same as 
            DataObj.unique_id.
        """
        collection = []

        for pk in pkeys:
            cmd = f"""
                MATCH (node)
                WHERE ID(node) = {pk}
                RETURN (node)
            """
            neo4j_data = self.execute_return(cmd)

            new_data_objects = self.convert_n4jdata_to_dataobjects(neo4j_data)
            collection.extend(new_data_objects)
        return collection


    def create_initial_ring(self, dataobjects: list) -> None:
        """ Takes in a list of dataobjects(packages.cleaning.data_object)
            and creates an initial root 'ring' in the Neo4j DB. See
            documentation for more information.
        """

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


    def get_ring_root(self) -> list:
        """ Get root ring of the neo4j db and return
            it in the form of a list of dataobjects
            (packages.cleaning.data_object).

            'Root ring' in this context means the nodes 
            which have no 'descendants'.
        """
        # // Getting the first ring
        cmd = """
            MATCH (strt:level_0)-[:TICK*]->(other:level_0)
            RETURN strt,other
        """
        result = self.execute_return(cmd)
        return self.convert_n4jdata_to_dataobjects(result)


    def get_ring_from_obj(self, obj) -> list:
        """ Uses a dataobject(packages.cleaning.data_object)
            to fetch the 'ring' (db structure) it is attached
            to, including itself. Retruns a list of dataobjects.
        """
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
 

    def get_level_from_node(self, obj) -> int:
        """ Uses a dataobject(packages.cleaning.data_object),
            which should be in the db, to find out which
            level it is in. 'Level' in this context refers
            to how many rings it is away from the root ring.
            If it's on the root ring, then level should be 0.

            Exception:
                If neo4j nodes do not have the correct level
                formatting (should be 'level_x'), where x is
                an integer.

            If the dataobject is not in the structure, then
            'None' is returned.
        """ 
        cmd = f"""
            MATCH (node)
            WHERE node.unique_id = '{obj.unique_id}'
            RETURN labels(node)
        """
        result = self.execute_return(cmd)

        for key in result[0]:
            label = result[0][key][0]
            stripped = label.strip("level_")
            return int(stripped)
    
 
    def create_node_endof_ring(self, obj_ring:list, obj_new:DataObj):
        """ Attempts to add a dataobject(packages.cleaning.data_object)
            to the end of a ring in the db stucture. Uses a list of 
            dataobjects to find the target ring, but actually uses
            the first item in that list to do the task. If 
            'obj_ring' is empty, then the task is aborted.
        """
        if not obj_ring:
            self.print_progress("tried to create obj at the end of a ring " +
                                "but ring is empty. Aborting")
            return
        # // Index doesn't matter because last node is autodetected.
        anyobj_in_ring = obj_ring[0]
        obj_last_in_ring = self.get_last_node_on_ring(anyobj_in_ring)[0]
        
        cmd = f"""
            MATCH (aliasnode_last)
            WHERE aliasnode_last.unique_id = '{obj_last_in_ring.unique_id}'
            MATCH (aliasnode_last)-[oldUpTie:UP]->(firstInRing)
            //MATCH (aliasnode_last)-[oldSelfTick:TICK]->(aliasnode_last)
        """
        if len(obj_ring) == 1: # // remove self tick from first DOWN insert.
            cmd += """
                MATCH (aliasnode_last)-[oldSelfTick:TICK]->(aliasnode_last)
                DETACH DELETE oldSelfTick
            """
        # // Queue creation of new node.
        target_level = self.get_level_from_node(obj_last_in_ring)
        cmd += self.create_tweet_node(alias="node_new", obj=obj_new, level=target_level, mode="return")
        # // Redo connections.
        cmd += """\n
            CREATE (aliasnode_last)-[:TICK]->(aliasnode_new)
            CREATE (aliasnode_new)-[:UP]->(firstInRing)
            DETACH DELETE oldUpTie//, oldSelfTick
        """
        self.cache_commands.append(cmd)


    def get_last_node_on_ring(self, obj: DataObj): # -> DataObj
        """ Uses a dataobject(packages.cleaning.data_obj) to
            get the last node(neo4j) on a ring in the db structure.
        """
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


    def create_node_below(self, obj_above, new_obj) -> None:
        """ Uses two dataobjects(packages.cleaning.data_object);
            the 'new_obj' is added to a new 'ring' under
            'obj_above'. 

            Recommended:
                Check first if obj_above has anything
                below it with self.get_node_below(),
                because nothing stops this method from
                creating a second ring, which will
                make some other methods buggy.

            Note: resulting command is added to cache_commands,
                    so a manual execution is required.
        """
        cmd = f"""
            MATCH (node_above)
            WHERE node_above.unique_id = '{obj_above.unique_id}'
        """
        target_level = self.get_level_from_node(obj_above) + 1
        cmd += self.create_tweet_node(
                alias="node_below", 
                obj=new_obj, 
                level=target_level, 
                mode="return"
        ) 
        # // Create ties:                         
        cmd += f"""
            CREATE (node_above)-[:DOWN]->(aliasnode_below)
            CREATE (aliasnode_below)-[:UP]->(node_above)
            CREATE (aliasnode_below)-[:TICK]->(aliasnode_below)
        """
        self.cache_commands.append(cmd)


    def get_descendants(self, dataobj) -> list:
        """ Get all descendants of a certain
            dataobj(packages.cleaning.data_object),
            meaning that every node/dataobj in
            all subrings will be returned. 
            Returns a list of dataobjects.
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
        """ Uses a dataobject(packages.cleaning.data_object) to
            get its relationship connectors(neo4j). Returns a 
            list of dictionaries, or other lists (depends on 'obj').
        """
        cmd = f"""
            MATCH (org), (other)
            WHERE org.unique_id = '{obj.unique_id}'
            MATCH (org)-[connector]-(other)
            RETURN other, connector, startNode(connector) as startRef
        """
        result = self.execute_return(cmd=cmd)
        return result


    def swap_nodes(self, objs_old:list, objs_new:list) -> None:
        """ Uses two lists of dataobjects(packages.cleaning.data_object)
            to swap their nodes in the db. Swapping is based on list index.
            Example [a,b] and [c,d];
                'a' will now be residing where 'c' used to be in
                the db structure and vice versa. Same with 'b' and 'd'.

            This function auto-executes, meaning that a manual cache
            execution isn't necessary.
        """

        cmd = ""
        # // Enumerate old objects for identification later on.
        for i, obj in enumerate(objs_old):
            cmd += f"MATCH (objOld{i}) WHERE objOld{i}.unique_id = '{obj.unique_id}'"

        # // Do swaps.
        for i in range(len(objs_old)):
            # // Format siminets such that the database can contain them.
            siminet_formatted = data_object_tools.siminet_to_txt(
                                    objs_new[i].siminet
                                )
            self.print_progress( # // Status update
                f"Que swap: '{objs_new[i].name}' -> node({objs_old[i].name})"
            )
            cmd += f"""
                SET objOld{i}.unique_id = '{objs_new[i].unique_id}'
                SET objOld{i}.name = "{objs_new[i].name}"
                SET objOld{i}.text = '{objs_new[i].text}'
                SET objOld{i}.siminet = "{siminet_formatted}"
            """
        # @ Auto-execute; might use this as an option.
        self.cache_commands.append(cmd)
        self.cache_execute(False)


    def get_node_next(self, obj, rel_type: str) -> list:
        """ Uses a dataobject(packages.cleaning.data_object) to
            find the 'next' node in the db. 'Next' is determined
            by the 'rel_type'.

            Supported reltypes are (others are exceptions):
                'TICK', 'UP', 'DOWN'

            Returns a list which should contain just one dataobj.
            More than one dataobj should raise suspicion of the
            db structure schema.
        """
        if rel_type not in ["TICK", "UP", "DOWN"]: # // supported moves
            raise ValueError(f"get_node_next: rel_type '{rel_type}' not supported.")
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
        """ Checks if an object is the last in the db structure.
            'Last' should be on the root ring, such that it
            has an 'UP' relationship pointing to the first.

        """
        root_ring_unsorted = self.get_ring_root()
        if root_ring_unsorted:
            root_ring_sorted = self.get_ring_from_obj(root_ring_unsorted[0])
            if root_ring_sorted:
                if obj.unique_id == root_ring_sorted[-1].unique_id:
                    return True
        return False
        



