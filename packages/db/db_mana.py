from packages.db.db_tools import GDBCom
from packages.similarity.process_tools import ProcessSimilarity

from packages.cleaning import data_object_tools # @ deb


class DBMana():


    def __init__(self, 
                 verbosity: bool = False, 
                 ringsize: int = 3,
                 static_ringsize: bool = False) -> None:
        """ Setup for this class where:
                - Verbosity for this class(verbosity_mana(ger)) is set.
                - Similarity tools are set. 
                - Default ringsize of db rings is set.
                - static_ringsize is set. True means that all rings must be at a fixed
                    size at all times, even if that means dropping some new nodes.
                    False means that ringsizes will always be a minimum of the ringsize 
                    property, but will be larger if a new node cannot be associated
                    with any nodes in current/destination ring. This means that no
                    new nodes will get dropped.
        """

        self.verbosity = verbosity

        self.ringsize = ringsize
        self.static_ringsize = static_ringsize

        self.dataobj_queue = []
        self.clockwork_current_node = None


    def setup_db_tools(self, verbosity: bool = False) -> None:
        """ Setting up db tools
        """
        self.gdbcom = GDBCom(verbosity=verbosity)
        self.gdbcom.setup()


    def setup_simi_tools(self, load_model: bool = True, verbosity: bool = False) -> None:
        """ Setting up similarity processing tools. Having its own method
            such that model load is easier to control (loading it every time
            a test occurs can be time consuming).
        """
        self.simitool = ProcessSimilarity(verbosity=verbosity)
        if load_model:
            self.simitool.load_model("glove-twitter-25")


    def cond_print(self, content: str) -> None:
        "Conditional print, where all module printouts occur only if self.verbosity = True"
        if self.verbosity: print(content)


    def queue_dataobj(self, dataobj) -> None:
        "Simply queue a new data object for processing."
        pass


    def check_queue_drop(self) -> None:
        """ Drop data objects form dataobj_queue if the queue is 
            getting too big.

            NOT IMPLEMENTED BUT:
                - Should send a signal to module caller.
        """ 
        pass


    def create_initial_ring(self, dataobjects: list, cached_siminet: bool = True) -> None:
        """ Creates the initial/main root ring in the db structure.
            Clears db before doing this.

            cached_siminet=True means that siminets of all objects are created and cached.
            This drastically improves the speed of the db, but will naturally increase
            the db size.
        """
        self.gdbcom.delete_all()
        if cached_siminet:
            for obj in dataobjects:
                obj.siminet_compressed = self.simitool.get_similarity_net(obj.text.split())
        self.gdbcom.create_initial_ring(dataobjects)
        self.gdbcom.cache_execute(_single_transaction = False)


    def autoinsertion(self, new_node, cached_siminet: bool = True, ) -> None:
        """ Inserts new DataObj into db.
            Note: NEEDS AN INITIAL RING.
            Creates a siminet for new_node and compares against the siminet
            of the nodes in rings. This is done recursively such that a new_node
            is inserted into any level of the db structure, as long as appropriate 
            matches are made.

            cached_siminet=True caches all siminets on db nodes, such that every node
            only needs one siminet creation. This will drastically improve the speed
            of the db, but will naturally increase the db size.
        """

        def insert(current_ring, current_object):
            ring_names = [obj.name for obj in current_ring] # // For cond_print.
            if len(current_ring) < self.ringsize:
                # // Always fill minimum ringsize.
                self.cond_print((f"Ring size {ring_names} not filled. " + 
                                 f"Just adding {current_object.name} at the end."))
                self.gdbcom.create_node_endof_ring(
                    obj_ring=current_ring, 
                    obj_new=current_object
                )
                self.gdbcom.cache_execute(_single_transaction = False)
                return
            else:
                # // Get index of most similar obj in current ring.
                # // Result might be None.
                result = self.simitool.get_top_simi_index(
                            new_object=current_object, 
                            other_objects=current_ring, 
                            degrees=3
                        )
                if result is None:
                    if not self.static_ringsize:
                        # // No similar objects found, just add to ring if 
                        # // the ringsize is dynamic.
                        self.gdbcom.create_node_endof_ring(
                            obj_ring=current_ring,
                            obj_new=current_object
                        )
                        self.gdbcom.cache_execute(_single_transaction = False)
                        self.cond_print(f"Extending ring {ring_names} with {current_object.name}")
                    else:
                        # // Drop current obj if ringsize is strict.
                        self.cond_print((f"No similarity between {current_object.name} +" 
                                         f"and ring: {ring_names}. Dropping obj."))
                    return
                target_obj = current_ring[result]
                below = self.gdbcom.get_node_below(obj=target_obj)
                        
                if not below: # // If target_obj has no nodes/rings under it, create it.
                    self.cond_print(f"new {current_object.name} below {target_obj.name}")
                    self.gdbcom.create_node_below(obj_above=target_obj, new_obj=current_object)
                    self.gdbcom.cache_execute(_single_transaction = False)
                else: # // Proceed to next ring.
                    new_ring = self.gdbcom.get_ring_from_obj(obj=below[0])
                    insert(
                        current_ring=new_ring, 
                        current_object=current_object
                    )

        if cached_siminet:
            new_node.siminet_compressed = self.simitool.get_similarity_net(new_node.text.split())
        ring_root = self.gdbcom.get_ring_root()
        if ring_root: # // Make sure that a ring root exists.
            insert(ring_root, new_node)


    def clockwork_traversal(self, sort:bool = True) -> None:
        """ Goes through the db structure, in a clockwork-type fashion.
            Not based on recursion because structure might change while
            doing these operations.
        """
        def set_first():
            unordered_root_ring = self.gdbcom.get_ring_root()
            ordered_root_ring = self.gdbcom.get_ring_from_obj(obj=unordered_root_ring[0])
            self.clockwork_current_node = ordered_root_ring[0]
        # // Set first node.
        if self.clockwork_current_node == None: set_first()
        # @ TODO: Re-introduce when one round is done
        while True:
            #input()# // @ for development
            self.cond_print(f"current name: '{self.clockwork_current_node.name}'")
            # // Go down as far as possible on each TICK.
            node_below = self.gdbcom.get_node_below(obj=self.clockwork_current_node)
            if node_below:
                self.clockwork_current_node = node_below[0]
                continue
            else:
                # // Check if this is the last node on ring.
                node_above = self.gdbcom.get_node_above(obj=self.clockwork_current_node)
                if not node_above: # // If that's not the case; tick and continue.
                    node_tick = self.gdbcom.get_node_tick(obj=self.clockwork_current_node)
                    if not node_tick: raise ValueError # // @ for development.
                    self.clockwork_current_node = node_tick[0]
                    continue
                else: # // Case: Last node on ring.
                    # // Check if current is the last node in db structure.
                    if self.gdbcom.check_if_last(self.clockwork_current_node): 
                        set_first()
                        print("LAST")
                        return # // @ Deb 
                        
                    node_tick = []
                    # // Empty node_tick means that next is UP. This can occur
                    # // multiple times, so keep trying.
                    print(f"node above: {node_above[0].name}") # @
                    while not node_tick:
                        if self.gdbcom.check_if_last(node_above[0]):
                            set_first()
                            print("LAST Z")
                            return
                        node_tick = self.gdbcom.get_node_tick(obj=node_above[0])
                        node_above = self.gdbcom.get_node_above(node_above[0])
                        print("UPWARDS LOOP")

                    # // Sort when the next node is UP, but only 
                    # // after next is calculated (block above).
                    if sort: self.clockwork_sort()

                    self.clockwork_current_node = node_tick[0]
                    if self.gdbcom.check_if_last(node_tick[0]):
                        set_first()
                        print("LAST M")
                        return
                    print("END OF TRAV")
                    continue
        

    # def clockwork_sort(self) -> None:
    #     # // guard no current ring
    #     if not self.clockwork_current_node: 
    #         #self.cond_print("clockwork_sort: No current ring, aborting")
    #         print("clockwork_sort: No current ring, aborting") # @ deb 
    #         return
    #     # // get ring, including above.
    #     ordered_root_ring = self.gdbcom.get_ring_from_obj(obj=self.clockwork_current_node)
    #     node_above = self.gdbcom.get_node_above(self.clockwork_current_node)
    #     ordered_root_ring.insert(0, node_above)
    #     return
        # // get connectors to above (a).
        # // Detach (a)
        # // Sort
        # // if sorted:
        # //    if new representative has below connectors
        # //        get below connectors of representative (b)
        # //        Detach (b)
        # // Attach representative (a)
        # // Re-introduce (b) and attach.

    def get_connectors_of(self, obj):

        cmd = f"""
            MATCH (org), (other)
            WHERE org.unique_id = '{obj.unique_id}'
            MATCH (org)-[connector]-(other)
            RETURN other, connector, startNode(connector) as startRef
        """
        return self.gdbcom.execute_return(cmd=cmd)

    def swap_node(self, obj_from, obj_to) -> None:
        # // Not necessary to replace a node with itself.
        if obj_from.unique_id == obj_to.unique_id: return

        # @@@ could do a faux check
        #content = backups[swap_index]
        siminet_formatted = data_object_tools.siminet_compressed_to_txt(obj_from.siminet_compressed)
        # // Not doing replacement within cypher like this:
        # //    'SET obj_to.name = obj_from.name'
        # // Because obj_a might have been swapped. This is the 
        # // reason behind having a backup list of dataobj
        # //
        # // Warning: while this happens, two nodes with the same ..
        # // unique id can exist.

        cmd = f""" 
            MATCH (obj_to)
            WHERE obj_to.unique_id = '{obj_to.unique_id}'

            SET obj_to.unique_id = '{obj_from.unique_id}'
            SET obj_to.name = "{obj_from.name}"
            SET obj_to.text = '{obj_from.text}'
            SET obj_to.siminet_compressed = "{siminet_formatted}"

        """
        self.gdbcom.cache_commands.append(cmd)
        
    def swap_nodes(self, objs_old, objs_new):

        cmd = ""

        for i, obj in enumerate(objs_old):
            cmd += f"MATCH (objOld{i}) WHERE objOld{i}.unique_id = '{obj.unique_id}'"

        for i in range(len(objs_old)):
            siminet_formatted = data_object_tools.siminet_compressed_to_txt(
                                    objs_new[i].siminet_compressed
                                )
            self.cond_print(
                f"Que swap: '{objs_new[i].name}' -> node({objs_old[i].name})"
            )
            cmd += f"""
                SET objOld{i}.unique_id = '{objs_new[i].unique_id}'
                SET objOld{i}.name = "{objs_new[i].name}"
                SET objOld{i}.text = '{objs_new[i].text}'
                SET objOld{i}.siminet_compressed = "{siminet_formatted}"
            """
        self.gdbcom.cache_commands.append(cmd)
        self.gdbcom.cache_execute(False)


    def clockwork_sort(self) -> None:
        # // Guard empty current node.
        if not self.clockwork_current_node: 
            self.cond_print("clockwork_sort: No current node, aborting")
            return
        # // Get ring, including above.
        ordered_root_ring = self.gdbcom.get_ring_from_obj(obj=self.clockwork_current_node)
        node_above = self.gdbcom.get_node_above(self.clockwork_current_node)[0]
        ordered_root_ring.insert(0, node_above)
        ring_old = ordered_root_ring # @ fix naming
        print(f"ORIGINAL: {[ obj.name for obj in ring_old]}")
        # // Attempt sorting by similarity.
        representative_result = self.simitool.get_representatives(
            objects=ring_old, cached_siminet=True
            )
        print(f"ORDERED: {[obj.name for obj in representative_result[1]]}")
        # // Skip if order in new and old ring is the same.
        if not representative_result[0]: # // Check order change.
            self.cond_print("clockwork_sort: ran sort but order has not changed.")
            return

        ring_new = representative_result[1]
        print(f"NEW REP: {ring_new[0].name}")
        self.swap_nodes(objs_old=ring_old, objs_new=ring_new)

    def event_loop(self) -> None:
        """ Alternating between autoinsertion, clockwork_sort, query and check_queue_drop.
            Created to be self-sufficient main loop of this class; run once and
            let it be.
        """
        pass