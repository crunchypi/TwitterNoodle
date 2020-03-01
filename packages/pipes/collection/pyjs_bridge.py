import asyncio
import websockets

from packages.pipes.collection.base import PipeBase
from packages.similarity.process_tools import ProcessSimilarity
from credentials import pyjs_bridge_ip, pyjs_bridge_port


class PyJSBridgePipe(PipeBase):
    def __init__(self,
                input: list,
                output: list, # @ Deb
                query: list,
                simitool: ProcessSimilarity,
                threshold_input:int, 
                threshold_output:int, 
                refreshed_data:bool, 
                verbosity:bool) -> None:

        self.simitool = simitool
        self.output = output
        self.query_queued = query
        self.query_ready = []

        super(PyJSBridgePipe, self).__init__(
                input=input,
                output=self.output,
                process_task=self.__task, 
                threshold_input=threshold_input, 
                threshold_output=threshold_output, 
                refreshed_data=refreshed_data, 
                verbosity=verbosity
        )
        print("pipe")

    def start(self):
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
        while True:
            self.check_query_update() # // Check if query is to be updated.
            next_data = self.calc_next_score()
            #print(next_data) # @ Deb
            if next_data != None: # // Only send if there is some data.
                await websocket.send(str(next_data))
            await asyncio.sleep(0.1)


    def confirm_str_lst(self, lst) -> bool:
        for item in lst:
            if type(item) is not str:
                self.cond_print("warn: query found a non-str.")
                return False
        return True


    def check_query_update(self):
        if type(self.query_queued) is not list: raise ValueError("query must be a list")
        if self.query_queued:
            if self.confirm_str_lst(self.query_queued):
                self.query_ready = self.simitool.get_similarity_net(
                    query=self.query_queued
                )
                self.query_queued.clear()


    def calc_next_score(self):
        if self.input:
            if self.query_ready:
                last_obj = self.input.pop()
                simi_score = self.simitool.get_score_compressed_siminet(
                    new=last_obj.siminet,
                    other=self.query_ready
                )
                self.output.append(simi_score) # // For monitor hooks.
                return simi_score
        return None


    def __task(self, element): # @ Dead code.
        return element


    def __del__(self):
        asyncio.get_event_loop().stop()