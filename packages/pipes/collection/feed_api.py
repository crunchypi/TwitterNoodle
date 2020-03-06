
from packages.pipes.collection.base import PipeBase
from packages.feed.tweet_feed import Feed

class FeedFromAPIPipe(PipeBase):

    """ This particular class gets tweepy tweets from
        the API(credentials must be set). As such,
        an input list is not required.

        Note: self.__task and process is redundant because
            1 - There is not input list.
            2 - Tweets go directly to output list.

            If this class is garbage collected, then
            the stream is automatically closed.
    """

    def __init__(self,
                track: list,
                output: list,
                threshold_input:int, 
                threshold_output:int, 
                refreshed_data:bool, 
                verbosity:bool) -> None:
        """ Setting required values, and passing to super.
            See docstring of this class and the base class
            for more information.
        """
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
        " Sets tweepy stream. See packages.feed for more information. "
        stream_collection = []
        feed = feed = Feed()
        self.listener = feed.live_get_listener(stream_collection)
        self.stream = feed.live_get_streamer(self.listener, track)
        return stream_collection
        

    def __task(self, element):
        " Redundant, will not be called. "
        return element

    def __del__(self):
        " Stops stream on garbage collection. "
        self.stream.disconnect() # // Stop stream