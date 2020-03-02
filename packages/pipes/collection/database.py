from packages.pipes.collection.base import PipeBase
from packages.db.db_mana import DBMana

class DBPipe(PipeBase):

    def __init__(self, 
                input: list,
                new_root_ring: bool,
                threshold_input:int = 200, 
                threshold_output:int = 200, 
                verbosity:bool = False) -> None:

        self.start_fresh = True
        self.setup()

        super(DBPipe, self).__init__(
                input=input,
                output=[],
                process_task=self.__task, 
                threshold_input=threshold_input, 
                threshold_output=threshold_output, 
                refreshed_data=False, 
                verbosity=verbosity
        )
        

    def setup(self):
        # @ config file for params?
        self.db_mana = DBMana()
        self.db_mana.setup_db_tools()
        self.db_mana.setup_simi_tools()  
        # // Check if there is a root ring. If there are none;
        # // signal creation, even if it was prohibited by
        # // the init. Adding new nodes without root ring 
        # // will lead to a crash.
        root_ring = self.db_mana.gdbcom.get_ring_root()
        if not root_ring: self.start_fresh = True
        self.db_event_loop = self.db_mana.event_loop()


    def __task(self, item):
        # // Taking control over output queue from base.
        self.output.append(item)
        # // If starting fresh; wait for initial nodes to collect.
        if self.start_fresh:
            if len(self.output) > 3: # @ Config
                initial_ring = []
                for x in range(3):
                    obj = self.output.pop()
                    initial_ring.append(obj)
                self.db_mana.create_initial_ring(
                    dataobjects=initial_ring
                )
                self.start_fresh = False
        else: # // Root ring exists
            if self.output:
                # // Pass data
                new_obj = self.output.pop()
                self.db_mana.dataobj_queue.append(new_obj)
                # // Try next, reset on fail.
                try:
                    next(self.db_event_loop)
                except StopIteration:
                    self.db_event_loop = self.db_mana.event_loop()

        return None

