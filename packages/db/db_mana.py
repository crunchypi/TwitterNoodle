from packages.db.db_tools import GDBCom
from packages.similarity.process_tools import ProcessSimilarity

from packages.cleaning import data_object_tools # @ deb
from packages.misc.custom_thread import CustomThread

# // @ add global siminet degree

class DBMana():



    def __init__(self, 
                 verbosity: bool = False, 
                 ringsize: int = 3,
                 static_ringsize: bool = False,
                 conservative_swaps: bool = True) -> None:
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
                - conservative_swaps = True means:
                    Swaps only new representatives and old rep in clockwork sort. 
                    False swaps all the nodes which have a new order in a rep swap.
                    
        """

        self.verbosity = verbosity

        self.ringsize = ringsize
        self.static_ringsize = static_ringsize
        self.conservative_swaps = True

        self.dataobj_queue = []
        self.dataobj_queue_overloaded = False
        self.dataobj_queue_max_threshold_soft = 100
        self.dataobj_queue_max_threshold_hard = 200

        self.clockwork_current_node = None

        # // Event-loop is looped and async.
        self.event_loop_enabled = True
        self.event_loop_thread = CustomThread(_task=self.event_loop, _is_looped=False)


    def setup_db_tools(self, verbosity: bool = False) -> None:
        """ Setting up db tools.
        """
        self.gdbcom = GDBCom(verbosity=verbosity)
        self.gdbcom.setup()


    def setup_simi_tools(self, load_model: bool = True, verbosity: bool = False) -> None:
        """ Setting up similarity processing tools. Having its own method
            such that model load is easier to control (loading it every time
            a test occurs can be time consuming).
        """
        self.simitool = ProcessSimilarity(verbosity=verbosity)
        if load_model: self.simitool.load_model("glove-twitter-25")


    def cond_print(self, content: str) -> None:
        "Conditional print, where all module printouts occur only if self.verbosity = True"
        if self.verbosity: print(content)


    def queue_dataobj(self, dataobj) -> None:
        "Simply queue a new data object for processing."
        self.dataobj_queue.append(dataobj)


    def check_queue_drop(self) -> None:
        """ Check dataobj_queue status.
            - If the length is reaching a soft limit, give a warn and 
              signal overload.
            - If the length is reaching a hard limit, give a warn,
                signal overload and drop.
            - If witin limits, signal green light.
        """
        # // Unnecessary re-definitions for better readability.
        current = len(self.dataobj_queue)
        hard = self.dataobj_queue_max_threshold_hard
        soft = self.dataobj_queue_max_threshold_soft

        if current >= hard:
            self.cond_print("check_queue_drop: hard threshold reached. Dropping obj.")
            self.dataobj_queue_overloaded = True
            self.dataobj_queue.pop(0) # @ consider doing this multiple times.
        elif current >= soft and current <= hard:
            self.cond_print("check_queue_drop: soft threshold reached")
            self.dataobj_queue_overloaded = True
        else:
            self.dataobj_queue_overloaded = False
        

    def create_initial_ring(self, dataobjects: list) -> None:
        """ Creates the initial/main root ring in the db structure.
            Clears db before doing this.
        """
        self.gdbcom.delete_all()
        self.gdbcom.create_initial_ring(dataobjects)
        self.gdbcom.cache_execute(_single_transaction = False)


    def autoinsertion(self, new_node) -> None:
        """ Inserts new DataObj into db.
            Note: NEEDS AN INITIAL RING.
            Creates a siminet for new_node and compares against the siminet
            of the nodes in rings. This is done recursively such that a new_node
            is inserted into any level of the db structure, as long as appropriate 
            matches are made.

            Exceptions: ValueError if no ring root exists in the db structure.
        """

        def insert(current_ring:list, current_object) -> None:
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
                    # // No similar objects found
                    if not self.static_ringsize:
                        # // Just add to ring if the ringsize is dynamic.
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
                        
                if not below: # // If target_obj has no nodes/rings under it, create one.
                    self.cond_print(f"new {current_object.name} below {target_obj.name}")
                    self.gdbcom.create_node_below(obj_above=target_obj, new_obj=current_object)
                    self.gdbcom.cache_execute(_single_transaction = False)
                else: # // Proceed to next ring.
                    new_ring = self.gdbcom.get_ring_from_obj(obj=below[0])
                    insert(
                        current_ring=new_ring, 
                        current_object=current_object
                    )

        ring_root = self.gdbcom.get_ring_root()
        if not ring_root: raise ValueError("Create ring root before insertion")
        insert(ring_root, new_node)


    def re_introduce_descendants_of(self, dataobj) -> None:
        """ Detach and delete dataobjects, and re-introduce them
            into the db structure.
        """
        # // Cache all descendants of dataobj and delete them from db.
        descendants = self.gdbcom.get_descendants(dataobj)
        self.cond_print(f"Reintroducing: {[node.name for node in descendants]}")
        self.gdbcom.delete_nodes(descendants)
        # // Re-introduce.
        for node in descendants:
            # // Do not create a new siminet for each node, since 
            # // siminets would have already been created if necessary.
            self.autoinsertion(new_node=node)    


    def clockwork_traversal(self, sort:bool = True, continuous:bool = False) -> GeneratorExit:
        """ Traverse database structure. Options:
                - Sort=True will start a sort at the end of each ring.
                - Continuous=True will traverse forever.

            NOTE: This is a generator method, will yield after a sort.
            
            Structure might change during recursion if sort=True but this
            should not affect recursion safety (due to consideration during
            implementation). 
        """
        def rec_task(current_ring:list) -> None:
            for node in current_ring:
                self.cond_print(f"--clockwork_traversal: current name is '{node.name}'")
                node_below = self.gdbcom.get_node_below(obj=node)
                if node_below:
                    self.cond_print("--clockwork_traversal: Going down.")
                    ring_below = self.gdbcom.get_ring_from_obj(obj=node_below[0])
                    # // Stack yield
                    yield from rec_task(current_ring=ring_below)

                if self.gdbcom.check_if_last(node): # // Exit if last.
                    self.cond_print("--clockwork_traversal: CYCLED.")
                    return

                # // Check if anything is above, sort if so (if that is specified).
                # // Yield only if sorting is enabled.
                node_above = self.gdbcom.get_node_above(obj=node)
                if node_above and sort: self.clockwork_sort(node); yield

        while True:
            unordered_root_ring = self.gdbcom.get_ring_root()
            ordered_root_ring = self.gdbcom.get_ring_from_obj(obj=unordered_root_ring[0])
            yield from rec_task(current_ring=ordered_root_ring) # // Yield stacks.
            if not continuous: return


    def clockwork_sort(self, current) -> None:
        """ This method takes a ring(including above node), sorts it, and
            swaps nodes accordingly
        """
        self.cond_print("   STARTING SORT")
        # // Guard empty node.
        if not current: 
            self.cond_print("clockwork_sort: No current node, aborting")
            return
        # // Get ring, including above.
        ordered_root_ring = self.gdbcom.get_ring_from_obj(obj=current)
        node_above = self.gdbcom.get_node_above(current)[0]
        ordered_root_ring.insert(0, node_above)
        ring_old = ordered_root_ring # @ fix naming
        self.cond_print(f"  ORIGINAL: {[ obj.name for obj in ring_old]}")
        # // Attempt sorting by similarity.
        representative_result = self.simitool.get_representatives(objects=ring_old)
        self.cond_print(f"  ORDERED: {[obj.name for obj in representative_result[1]]}")
        # // Skip if order in new and old ring is the same.
        if not representative_result[0]: # // Check order change.
            self.cond_print("   clockwork_sort: ran sort but order has not changed.")
            return

        ring_new = representative_result[1]
        # // Check if representative has changed
        if ring_new[0].unique_id == ring_old[0].unique_id:
            # // If so, just re-introdue rings below least rep.
            self.cond_print("   Order changed, but rep is the same. Re-introducing least rep.")
            self.re_introduce_descendants_of(ring_new[-1])
        else:
            # // Else re-introduce and do swaps.
            self.cond_print(f"  NEW REP: {ring_new[0].name}, OLD REP:{ring_old[0].name}")
            self.re_introduce_descendants_of(ring_new[0])
            if self.conservative_swaps:     
                first_new = ring_new[0]
                first_old = ring_old[0]
                self.gdbcom.swap_nodes(
                    objs_old=[first_old, first_new], 
                    objs_new=[first_new, first_old])
            else: 
                self.gdbcom.swap_nodes(objs_old=ring_old, objs_new=ring_new)


    def query_auto(self, q_dataobj) -> list:

        ring_root = self.gdbcom.get_ring_root()
        if not ring_root: raise ValueError("No ring root.")

        def rec_task(current_ring:list) -> list:
            collection = []
            similar_other_index = self.simitool.get_top_simi_index(
                                    new_object=q_dataobj, 
                                    other_objects=current_ring, 
                                    degrees=3
            )
            if similar_other_index is not None:
                # // If there exists a similar other
                # // on current ring -> add whole ring
                collection.extend(current_ring)
                node_below = self.gdbcom.get_node_below(
                    obj=current_ring[similar_other_index]
                )
                # // Only continue recursion if there are more
                # // rings below the most similar obj/node.
                if node_below:
                    ring_below = self.gdbcom.get_ring_from_obj(obj=node_below[0])
                    rec_result = rec_task(current_ring=ring_below)
                    if rec_result: collection.extend(rec_result)
            return collection

        return rec_task(current_ring=ring_root)


    def query_threshold_selective(self, q_siminet:list, threshold:float) -> list:
        """ Query by siminet and threshold: goes into sub-rings
            of those nodes which fall under this criteria:
                SimilarityScore(siminet, other) > threshold.
        """

        ring_root = self.gdbcom.get_ring_root()
        if not ring_root: raise ValueError("No ring root.")

        def rec_task(current_ring:list):
            collection = []
            # // Add any node from current ring if the node 
            # // satisfies the similarity threshold.
            for obj in current_ring:
                score = self.simitool.get_score_compressed_siminet(
                    new=q_siminet, 
                    other=obj.siminet) 
                if score >= threshold:
                    collection.append(obj)

            # // Go through similar nodes and get do recursion.
            rec_collection = []
            for obj in collection:
                node_below = self.gdbcom.get_node_below(obj=obj)
                if node_below:
                    ring_below = self.gdbcom.get_ring_from_obj(obj=node_below[0])
                    rec_result = rec_task(ring_below)
                    if rec_result: rec_collection.extend(rec_result)

            collection.extend(rec_collection)
            return collection

        return rec_task(ring_root)


    def query_threshold_all(self, q_siminet:list, threshold:float) -> list:
        """ Goes through the entire db structure and adds nodes 
            if they satisfy the similarity 'threshold' of
            'q_siminet'
        """
        ring_root = self.gdbcom.get_ring_root()
        if not ring_root: raise ValueError("No ring root.")

        def rec_task(current_ring:list) -> list:
            collection = []

            for obj in current_ring:
                score = self.simitool.get_score_compressed_siminet(
                    new=q_siminet, 
                    other=obj.siminet) 
                if score >= threshold:
                    collection.append(obj)

                node_below = self.gdbcom.get_node_below(obj=obj)
                if node_below:
                    ring_below = self.gdbcom.get_ring_from_obj(obj=node_below[0])
                    rec_result = rec_task(ring_below)
                    if rec_result: collection.extend(rec_result)

            return collection

        return rec_task(ring_root)


    def event_loop(self) -> None:
        """ Alternating between autoinsertion, clockwork_sort, query and check_queue_drop.
            Created to be self-sufficient main loop of this class; run once and
            let it be.
            NOTE: Meant to be ran in async (using custom_thread)
        """
        
        sort_generator = self.clockwork_traversal(sort=True, continuous=False)
   
        while self.event_loop_enabled: 
            self.check_queue_drop()
            # // Insert new
            if self.dataobj_queue:
                self.cond_print("event_loop: Started autoinsertion")
                new_node = self.dataobj_queue.pop(0)
                self.autoinsertion(new_node=new_node)
                self.cond_print("event_loop: Ended autoinsertion")
                print(f"Added '{new_node.name}'")
            try:
                self.cond_print("event_loop: Started Sort")
                next(sort_generator)
                self.cond_print("event_loop: Ended Sort")
            except StopIteration:
                self.cond_print("event_loop: Restarted Sort")
                sort_generator = self.clockwork_traversal(sort=True, continuous=False)


    def start_event_loop(self) -> None:
        self.cond_print("Starting async event loop")
        self.event_loop_thread.run()
        

    def stop_event_loop(self) -> None:
        print("Stopping event loop")
        self.event_loop_thread.stop()
        self.event_loop_enabled = False