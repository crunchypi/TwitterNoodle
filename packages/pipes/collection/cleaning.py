from packages.pipes.collection.base import PipeBase
from packages.cleaning import data_object_tools
from packages.cleaning.basic_cleaner import BasicCleaner

class CleaningPipe(PipeBase):

    def __init__(self, 
                input: list,
                output: list,
                threshold_input:int = 200, 
                threshold_output:int = 200, 
                refreshed_data:bool = True, 
                verbosity:bool = False) -> None:

        super(CleaningPipe, self).__init__(
                input=input,
                output=output,
                process_task=self.__task, 
                threshold_input=threshold_input, 
                threshold_output=threshold_output, 
                refreshed_data=refreshed_data, 
                verbosity=verbosity
        )


    def __task(self, item):
        sentiment_range = [-1.0,1.0]
        new_data_obj = data_object_tools.convert_tweet2dataobj(item)
        BasicCleaner.autocleaner(new_data_obj, sentiment_range, self.verbosity)
        return new_data_obj

