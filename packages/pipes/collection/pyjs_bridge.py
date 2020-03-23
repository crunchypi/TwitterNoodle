import asyncio
import websockets
import threading

from packages.pipes.collection.base import PipeBase
from packages.similarity.process_tools import ProcessSimilarity
from credentials import pyjs_bridge_ip, pyjs_bridge_port


class PyJSBridgePipe(PipeBase):

    """ This class is responsible for sending floats over
        localhost, which is meant to be taken from a JS
        front-end.

        IMPORTANT: This class is specialised:
            It expects a dataobject(packages.cleaning.data_object)
            from the input list, which is compared with a query.
            It is assumed that these dataobjects have siminets
            attached (packages.similarity.process_tools).
            Input expected to come from the output of pipe:
                packages.pipes.collection.simi

            The query must be a list of strings(checked), which
            will be converted to a siminet. This siminet
            will be compared with the siminet of new objects
            coming from the input list, to create a similarity
            score(float) which goes into the output list.

            Floats from the output list will be sent over
            websockets to any front-end. This task will
            be activated on connection.

            The query can be updated at any time; that is 
            automatically processed. This feature is currently
            (060320) unused but will be useful if this class
            is extended to take new queries from a front-end.
    """

    def __init__(self,
                previous_pipe,
                query: list,
                threshold_output:int, 
                verbosity:bool) -> None:
        """ Setting required values, and passing to super.
            See docstring of this class and the base class
            for more information.

            NOTE 1: Simitool must be an instance of
                packages.similarity.process_tools.ProcessSimilarity.
                This is implemented this way because the simi tool
                requires a loaded word2vec model, but it is assumed
                that it is already loaded into the runtime (input list
                should contain list of dataobjects with a simi net attached).
                This is purely for optimisation purposes, as loading a
                w2v model twice seems wasteful.

            NOTE 2:
                The main functionality (websockets) must be explicitly started
                from the outside, by calling the 'start' method, which uses
                asyncio.
        """

        super(PyJSBridgePipe, self).__init__(
                previous_pipe=previous_pipe,
                process_task=self.__task, 
                threshold_output=threshold_output, 
                verbosity=verbosity
        )

        self.query_queued = query # // For queries waiting to be transformed.
        self.query_ready = []   # // Transformed queries (siminets)
        self.set_simitool()
        self.foreign_data_queue = []
        self.thread_active = False


    def set_simitool(self):
        prev_pipe = self.previous_pipe
        # // Going through stack.
        while True:
            # // Going through properties.
            for key in prev_pipe.__dict__.keys():
                inst = prev_pipe.__dict__.get(key)
                # // Find ProcessSimilarity and check for w2v model.
                if isinstance(inst, (ProcessSimilarity)):
                    if inst.w2v_model:
                        self.simitool = inst
                        return
            # // Update.
            if prev_pipe.previous_pipe:
                prev_pipe = prev_pipe.previous_pipe
        # // If no simitool was found, make one.
        if not self.simitool:
            self.simitool = ProcessSimilarity()
            self.simitool.load_model()


    def start(self):
        "Starts asyncio and websockets"
        asyncio.set_event_loop(asyncio.new_event_loop())
        start_server = websockets.serve(
            self.serve_loop, 
            pyjs_bridge_ip, 
            pyjs_bridge_port
        )
        asyncio.get_event_loop().run_until_complete(start_server)
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            asyncio.get_event_loop().stop()


    async def serve_loop(self, websocket, path):
        """ Eventloop for websockets server, which
            sends similarity scores (see class docstring)
            over the network.
            This eventloop also checks for new queries.
        """
        while True:
            self.check_query_update() # // Check if query is to be updated.
            next_data = self.calc_next_score()
            if next_data != None: # // Only send if there is some data.
                await websocket.send(str(next_data))
            await asyncio.sleep(0.1)


    def confirm_str_lst(self, lst:list) -> bool:
        "Confirms that a list only contains strings"
        for item in lst:
            if type(item) is not str:
                self.cond_print("warn: query found a non-str.")
                return False
        return True


    def check_query_update(self):
        """ Checks for new queries and updates accordingly
            by creating a similarity net (see class docstring)
            from that query. New queries are moved from
            self.query_queued to self.query_ready.
        """
        if type(self.query_queued) is not list: raise ValueError("query must be a list")
        if self.query_queued:
            if self.confirm_str_lst(self.query_queued):
                self.query_ready = self.simitool.get_similarity_net(
                    query=self.query_queued
                )
                self.query_queued.clear()


    def calc_next_score(self):
        """ Uses similarity tool (see class docstring) to calculate
            the similarity between query and new dataobjects.
            Pushes new scores to self.output.
        """
        if self.foreign_data_queue:
            if self.query_ready:
                last_obj = self.foreign_data_queue.pop()
                simi_score = self.simitool.get_score_compressed_siminet(
                    new=last_obj.siminet,
                    other=self.query_ready
                )
                self.output.append(simi_score) # // For monitor hooks.
                return simi_score
        return None


    def __task(self, element):
        "Redundant but required"
        if not self.thread_active:
            network_thread = threading.Thread(target=self.start)
            network_thread.start()
            self.thread_active = True
        if element:
            self.foreign_data_queue.append(element)
        return None


    def __del__(self):
        "Stops event loop of asyncio on de-ref."
        asyncio.get_event_loop().stop()