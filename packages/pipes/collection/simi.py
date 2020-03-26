from packages.pipes.collection.base import PipeBase
from packages.similarity.process_tools import ProcessSimilarity

class SimiPipe(PipeBase):

    """ This particular pipe has a concise job:
            - Pull dataobj from self.previous_pipe
            - Add siminet to dataobj
            - Pass dataobj with siminet to self.output.
        
        Parlance:
            dataobj= An object which contains twitter data.
                        packages.cleaning.data_object
            siminet= A tree structure composed of related words.
                        created at: packages.similarity.process_tools
            simitool= Instance which creates siminets.
    
        NOTE: An init of this class will create an instance
            of simitool. This will load a w2v model, which 
            can take a while.
    """
    
    def __init__(self, 
                previous_pipe,
                threshold_output:int = 200,
                verbosity:bool = False,
                recursion_level:int = True) -> None:
        """ Setting required values, and passing to super.
            See docstring of base class for more information.

            NOTE: Beware; loads simitool with a word2vec model.
            See class docstring for more information.
        """
        super(SimiPipe, self).__init__(
                previous_pipe=previous_pipe,
                process_task=self.__task,
                threshold_output=threshold_output,
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
        