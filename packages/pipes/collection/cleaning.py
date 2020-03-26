from packages.pipes.collection.base import PipeBase
from packages.cleaning import data_object_tools
from packages.cleaning.basic_cleaner import BasicCleaner

class CleaningPipe(PipeBase):

    """ Cleaning pipe is a subclass of PipeBase and
        is meant to:
            1 - Take 'data'* from self.previous_pipe.
                    (data = tweepy tweet objects)
            2 - Covert it to dataobjects.
                    (dataobjects = packages.cleaning.data_object)
            3 - Perform NLP cleaning.
            4 - Pass result to self.output

        Action done by self.process()
    """

    def __init__(self, 
                previous_pipe,
                threshold_output:int = 200,
                verbosity:bool = False) -> None:
        """ Setting required values, and passing to super.
            See docstring of the baseclass init docstring
            for parameter details.
        """
        super(CleaningPipe, self).__init__(
                previous_pipe=previous_pipe,
                process_task=self.__task, 
                threshold_output=threshold_output,
                verbosity=verbosity
        )


    def __task(self, item):
        """ Called by baseclass process();
            takes an 'item' which should be a tweepy
            tweet, converts it to a data object (see
            packages.cleaning.data_object), cleans it with
            packages.cleaning.basic_cleaner and returns
            that cleaned dataobject, which is pushed
            by the baseclass to self.output list.
        """
        if item:
            sentiment_range = [-1.0,1.0]
            new_data_obj = data_object_tools.convert_tweet2dataobj(item)
            BasicCleaner.autocleaner(new_data_obj, sentiment_range, self.verbosity)
            return new_data_obj

