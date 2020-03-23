from packages.pipes.collection.base import PipeBase
from packages.cleaning import data_object_tools
from packages.cleaning.basic_cleaner import BasicCleaner

class CleaningPipe(PipeBase):

    """ Cleaning pipe is a subclass of PipeBase and
        is meant to take an input(list) of tweepy tweets.
        On self.process(), these tweets will be converted
        to dataobjects(packages.cleaning.data_object),
        cleaned(packages.cleaning.basic_cleaner) and
        appended to the output list.

        self.process() will do it with one item at a 
        time.
    """

    def __init__(self, 
                previous_pipe,
                threshold_output:int = 200,
                verbosity:bool = False) -> None:

        """ Setting required values, and passing to super.
            See docstring of this class and the base class
            for more information.
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

