
from packages.pipes.collection.base import PipeBase
from packages.feed.tweet_feed import Feed

class FeedFromDiskPipe(PipeBase):
    def __init__(self,
                filepath: str,
                output: list,
                threshold_input:int, 
                threshold_output:int, 
                refreshed_data:bool, 
                verbosity:bool) -> None:

        super(FeedFromDiskPipe, self).__init__(
                input=self.fetch_input(filepath),
                output=output,
                process_task=self.__task, 
                threshold_input=threshold_input, 
                threshold_output=threshold_output, 
                refreshed_data=refreshed_data, 
                verbosity=verbosity
        )

    def fetch_input(self, filepath:str):
        feed = Feed()
        return feed.disk_get_tweet_queue(filepath)

    def __task(self, element):
        return element # @ add streaming