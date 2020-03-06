
from packages.pipes.collection.base import PipeBase
from packages.feed.tweet_feed import Feed

class FeedFromDiskPipe(PipeBase):

    """ This particular class gets a list of pickled
        tweepy tweets from a local dataset. As such,
        an input list is not required, though a filepath
        is.

        Note: self.__task and process is redundant because
            1 - There is not input list.
            2 - Tweets go directly to output list.
    """

    def __init__(self,
                filepath: str,
                output: list,
                threshold_input:int, 
                threshold_output:int, 
                refreshed_data:bool, 
                verbosity:bool) -> None:
        """ Setting required values, and passing to super.
            See docstring of this class and the base class
            for more information.
        """

        super(FeedFromDiskPipe, self).__init__(
                input=self.fetch_input(filepath),
                output=output,
                process_task=self.__task, 
                threshold_input=threshold_input, 
                threshold_output=threshold_output, 
                refreshed_data=refreshed_data, 
                verbosity=verbosity
        )

    def fetch_input(self, filepath:str) -> list:
        """ Fetches a list of tweepy tweets from path.
            See docstring from this class and from
            packages.feed.tweet_feed for more information.
        """
        feed = Feed()
        return feed.disk_get_tweet_queue(filepath)

    def __task(self, element):
        " Redundant. Required but not called. "
        return element