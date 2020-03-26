import asyncio
import websockets
import threading

from packages.pipes.collection.base import PipeBase
from packages.similarity.process_tools import ProcessSimilarity
from credentials import pyjs_bridge_ip, pyjs_bridge_port


class PyJSBridgePipe(PipeBase):

    """ This is a special class with one responsebility;
        to send data to a front-end through WebSockets.
        This involves a lengthy process, though.

        Parlance:
            dataobj= An object which contains twitter data.
                        packages.cleaning.data_object
            siminet= A tree structure composed of related words.
                        created at: packages.similarity.process_tools
            simitool= Instance which creates siminets.

        Process:
            - Create siminets from a list of strings (AKA query)
                provided in self.init.
            - Infrastructure for query update exists but is not used
                at the data of writing. This infrastructure
                accepts a new query in self.query_queued.
                This list is used for staging and is eventually
                processed and moved to self.query_ready.

            - Take dataobjs from self.previous_pipe; those
                dataobjects need to have siminets ..
            - Then compare siminets those dataobjs against the
                siminets of self.query_ready. This comparison
                is done by the simi class. Result is a float
            - Float is sent over WebSockets if a connection
                is established.

        NOTE 1:
            This class can autodetect a simitool in 
            previous_pipe stack (all). It is assumed that
            SimiPipe(packages.pipes.collection.simi) is
            in the same pipeline as this class. If this is 
            not true, and a simitool is not autodetected,
            then it is created. On creation a w2v model 
            is loaded, which can take some amount of time.
        NOTE 2:
            This class spawns a thread which uses asyncio
            with WebSockets.

    """

    def __init__(self,
                previous_pipe,
                query: list,
                threshold_output:int, 
                verbosity:bool) -> None:
        """ Setting required values, and passing to super.
            See docstring of base class for more information.

            New param:
                'query'= This is used to create siminets which
                are compared against the siminets in dataobjs 
                pulled from self.previous_pipe. See class
                docstring for more information.
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
        self.thread_active = False # // Used to spawn thread exactly once.


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
        """ This method call does two things:
                - Spawns one thread on first call,
                    which activates WebSockets. 
                - Moves 'element' param to 
                    self.foreign_data_queue.
                    'element' is expected to be
                    a dataobj with a siminet.
                    See class docstring for more info.
        """
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