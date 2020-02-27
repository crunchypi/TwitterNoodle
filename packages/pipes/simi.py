from packages.pipes.base import PipeBase
from packages.similarity.process_tools import ProcessSimilarity

class SimiPipe(PipeBase):

    
    def __init__(self, 
                input: list,
                output: list,
                threshold_input:int = 200, 
                threshold_output:int = 200, 
                refreshed_data:bool = True, 
                verbosity:bool = False,
                recursion_level:int = True) -> None:

        super(SimiPipe, self).__init__(
                input=input,
                output=output,
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
        if item.text == None:
            raise ValueError("Expected DataObject.text, found None")
        query = item.text.split()
        item.siminet = self.simitool.get_similarity_net(
            query=query,
            max_recursion=self.recursion_level
        )
        return item
        