from packages.pipes.collection.base import PipeBase
from packages.similarity.process_tools import ProcessSimilarity

class SimiPipe(PipeBase):

    """ This particular pipe has only one job:
        Expects an input list where only 
        dataobjects(packages.cleaning.data_object)
        are pushed. It is reccommended that
        the dataobj.text fields are pre-cleaned with
        packages.cleaning.basic_cleaner.

        DataObj are pulled from input list,
        get a siminet (see packages.similarity.process_tools)
        attached to DataObj.siminet field, and are
        pushed to the output list.

        Note: An instance of this class will automatically
        create an instance of packages.similarity.process_tools,
        which will load a word2vec model. This might take some time.
    """
    
    def __init__(self, 
                previous_pipe,
                threshold_input:int = 200, 
                threshold_output:int = 200, 
                refreshed_data:bool = True, 
                verbosity:bool = False,
                recursion_level:int = True) -> None:
        """ Setting required values, and passing to super.
            See docstring of this class and the base class
            for more information.

            NOTE: Beware; loads a word2vec model.
        """
        super(SimiPipe, self).__init__(
                previous_pipe=previous_pipe,
                process_task=self.__task, 
                threshold_input=threshold_input, 
                threshold_output=threshold_output, 
                refreshed_data=refreshed_data, 
                verbosity=verbosity
        )
        # // Setup and load tools (model load might take a few seconds).
        self.simitool = ProcessSimilarity(verbosity=verbosity)
        self.simitool.load_model()

        self.recursion_level = recursion_level


    def __task(self, item):
        """ Attaches new siminets to dataobjects from
            input list before pushing them (dataobj) to
            output list. See class docstring for more 
            information.

            NOTE: will crash if dataobjects do not have 
                valid text fields.
        """
        if not item: return
        
        if item.text == None:
            raise ValueError("Expected DataObject.text, found None")
        query = item.text.split()
        item.siminet = self.simitool.get_similarity_net(
            query=query,
            max_recursion=self.recursion_level
        )
        return item
        