
from packages.pipes.collection.base import PipeBase
from packages.feed.tweet_feed import Feed

class FeedFromAPIPipe(PipeBase):

    """ This particular class gets tweepy tweets from
        the API(credentials must be set). As such,
        a previous_pipe is not required.

        Note: self.__task and process is redundant because
            1 - There is not previous pipe.
            2 - Tweets go directly to output list.

            If this class is garbage collected, then
            the stream is automatically closed.
    """

    def __init__(self,
                track: list,
                threshold_output:int = 200, 
                verbosity:bool = False) -> None:
        """ Setting required values, and passing to super.
            See docstring of baseclass for more information
            about params.
            New param:
                'track'= what the Twitter API will send
                back. If track=['cats'] then tweets
                collected will likely be related to cats..
        """
        super(FeedFromAPIPipe, self).__init__(
                previous_pipe=None,
                process_task=self.__task, 
                threshold_output=threshold_output, 
                verbosity=verbosity
        )
        self.set_stream_fetch_input(track=track)

    def set_stream_fetch_input(self, track:list) -> None:
        " Sets tweepy stream. See packages.feed for more information. "
        feed = Feed()
        self.listener = feed.live_get_listener(self.output)
        self.stream = feed.live_get_streamer(self.listener, track)
    
    def __task(self, element):
        " Redundant, will not be called. "
        return None

    def __del__(self):
        " Stops stream on garbage collection. "
        self.stream.disconnect()