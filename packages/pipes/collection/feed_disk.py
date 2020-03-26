
import pickle
from packages.pipes.collection.base import PipeBase
from packages.feed.tweet_feed import Feed

class FeedFromDiskPipe(PipeBase):

    """ This particular class uses datasets created with
        packages.dataset_tool.generate_dataset.
        The dataset file will be opened and read
        with a generator. Each time self.process 
        (base class) is called, a new object is pulled
        from the dataset class and added to self.output.
        Format of dataset:
            pickeled list of objects.
    """

    def __init__(self,
                filepath: str,
                threshold_output:int,
                verbosity:bool) -> None:
        """ Setting required values, and passing to super.
            See docstring of base class for more information.
            New param:
                'filepath'= points to a dataset file.
                See more information in class docstring.
                NOTE: file must not be .zip
        """
        super(FeedFromDiskPipe, self).__init__(
                previous_pipe=None,
                process_task=self.__task, 
                threshold_output=threshold_output, 
                verbosity=verbosity
        )

        self.unpickle_generator = self.get_unpickle_generator(
            filepath=filepath
        )

    def get_unpickle_generator(self, filepath:str):
        """ Used to create a generator and add it 
            as a class property. On call,
            the generator will return an item
            from a pickled iterator.
        """
        with open(filepath, mode="rb") as file:
            try:
                content = pickle.load(file)
                for item in content:
                    yield item
            except EOFError:
                pass


    def __task(self, element):
        """ Calls generator object self.unpickle_generator 
            to get some item. This item is then returned
            such that caller of this method (baseclass
            method 'process' can push the item to self.output).
        """
        try:
            return next(self.unpickle_generator)

        except StopIteration:
            pass