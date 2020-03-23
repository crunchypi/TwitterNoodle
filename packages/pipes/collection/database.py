from packages.pipes.collection.base import PipeBase
from packages.db.db_mana import DBMana

class DBPipe(PipeBase):

    """ This pipe assumes an input list which
        gets dataobjects(packages.cleaning.data_object)
        which are cleaned(packages.cleaning.basic_cleaner)
        and have siminets attached(packages.similarity.process_tools).

        The action (baseclass.)process() works with self.__task like this:
            - Move oldest item from input list and put it into
              self.output. This is handled here.
               
            - Checks if new root_ring should be set (see docs), based
                on self.new_root_ring.
                - If that is the case wait until there are 3 objects
                  in self.output. When that is the case, take all of them
                  and create a new root ring in the db.
            - Alternating task:
                1 - Take a dataobj from output list and make the dbmanager
                    (packages.db.db_mana) insert that into the db structure.
                2 - Make the dbmanager sort the db structure 
                    (chunked, with generator).
    """

    def __init__(self, 
                previous_pipe,
                start_fresh,
                threshold_input:int = 200, 
                threshold_output:int = 200, 
                verbosity:bool = False) -> None:
        """ Initialises with required data; see docstring
            of this- and base class for more info.

            Note: start_fresh=True clears the db.
            If this is set to False, and there is 
            no root_ring, then an override will occur
            which defaults to True.
        """
        self.start_fresh = start_fresh
        self.setup()

        super(DBPipe, self).__init__(
                previous_pipe=previous_pipe,
                process_task=self.__task, 
                threshold_input=threshold_input, 
                threshold_output=threshold_output, 
                refreshed_data=False, 
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
        # // Check if there is a root ring. If there are none;
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
        """ Alternates between db insertion and db sorting.
            See class docstring for more information.
        """
        if item:
            # // Drop objects with lack of siminet.
            if not item.siminet:
                self.cond_print(
                    "DB pipe found item with no siminet. Dropping."
                )
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

