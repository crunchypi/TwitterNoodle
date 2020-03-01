
from packages.pipes.collection.base import PipeBase
from packages.feed.tweet_feed import Feed

class FeedFromAPIPipe(PipeBase):
    def __init__(self,
                track: list,
                output: list,
                threshold_input:int, 
                threshold_output:int, 
                refreshed_data:bool, 
                verbosity:bool) -> None:

        super(FeedFromAPIPipe, self).__init__(
                input=self.set_stream_fetch_input(track),
                output=output,
                process_task=self.__task, 
                threshold_input=threshold_input, 
                threshold_output=threshold_output, 
                refreshed_data=refreshed_data, 
                verbosity=verbosity
        )

    def set_stream_fetch_input(self, track):
        stream_collection = []
        feed = feed = Feed()
        self.listener = feed.live_get_listener(stream_collection)
        self.stream = feed.live_get_streamer(self.listener, track)
        return stream_collection
        

    def __task(self, element):
        return element # @ add streaming

    def __del__(self):
        self.stream.disconnect() # // Stop stream