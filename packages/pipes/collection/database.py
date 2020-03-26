from packages.pipes.collection.base import PipeBase
from packages.db.db_mana import DBMana

class DBPipe(PipeBase):

    """ 
    This pipe is a subclass of PipeBase and
    has two primary responsebilities:
        - Move data to Neo4j DB, see point 1 below.
        - Sort data in Neo4j DB, see point 2 below.

    Clarification first:
        - dataobj = packages.cleaning.data_object
        - siminet = v2w tree structure created by
            packages.pipes.collection.simi AND/OR
            packages.similarity.process_tools.

    1 : 
        - Takes dataobj from self.previous_pipe
            (dataobj must have a siminet).
            - Either: caches it to create a new
                DB ring (schema purpose), if required.
                This caching is done until a minimum
                ring size can be created.
            - OR: uses the db_manager class to 
                automatically insert the new node.
    2 : 
        calls db_manager to do sorting. This is done
        with a generator, which makes it cheap.


    Action done automatically by self.process()
    """

    def __init__(self, 
                previous_pipe,
                start_fresh:bool,
                threshold_output:int,
                verbosity:bool = False) -> None:
        """ Initialises with required data; see docstring
            of base class init for more info.
            New param:
                'start_fresh'=True clears the db
                before making entries. If there
                is no root ring in the db (schema),
                then a new root ring will be created
                anyway.
        """
        self.start_fresh = start_fresh
        self.setup()

        super(DBPipe, self).__init__(
                previous_pipe=previous_pipe,
                process_task=self.__task, 
                threshold_output=threshold_output,
                verbosity=verbosity
        )
        

    def setup(self):
        """ Sets up database tools, will fail
            if the neo4j db server isn't up,
            or the credentials are set incorrectly.

            Also checks if there is a root ring, see comment 
            below and init docstring for more information.
        """
        self.db_mana = DBMana()
        self.db_mana.setup_db_tools()
        self.db_mana.setup_simi_tools()  
        # // Check if there is a root ring. If there is none;
        # // signal creation, even if it was prohibited by
        # // the init. Adding new nodes without root ring 
        # // will lead to a crash.
        root_ring = self.db_mana.gdbcom.get_ring_root()
        if not root_ring: self.start_fresh = True
        # // Set first sorting generator
        self.mana_sort_generator = self.db_mana.clockwork_traversal(
            sort=True,
            continuous=False
        )



    def __task(self, item):
        """ Does db insertion and db sorting.
            Expects 'item' arg to be dataobj
            with siminet (see class docstring)
        """
        if item:
            # // Drop objects with lack of siminet.
            if not item.siminet:
                self.cond_print( "DB pipe found item" 
                                "with no siminet. Dropping.")
                return None
            # // Taking control over output queue from base.
            self.output.append(item)
        # // If starting fresh; wait for initial nodes to collect.
        if self.start_fresh:
            if len(self.output) > 3: # @ Config
                initial_ring = []
                for _ in range(3):
                    obj = self.output.pop()
                    initial_ring.append(obj)
                self.db_mana.create_initial_ring(
                    dataobjects=initial_ring
                )
                self.start_fresh = False
        else: # // Root ring exists
            # // Insert new node.
            if self.output:
                new_obj = self.output.pop()
                self.db_mana.autoinsertion(new_node=new_obj)
            # // Do sorting.
            try:
                next(self.mana_sort_generator)
            except StopIteration: # // Reset generator.
                self.mana_sort_generator = self.db_mana.clockwork_traversal(
                    sort=True,
                    continuous=False
                )
        return None

