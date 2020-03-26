# // TODO:threshold handling?

class PipeBase():

    """ This class is meant to be a base class for 
        certain 'pipes' which are used to construct
        the 'pipelines' for this project.

        Idea is to have pipes as interfaces for the 
        'lower-level' functionality of this project.
        For example: Data cleaning.

        Each time process() is called, data is pulled
        from a previous pipe(property), if there is
        one, process the data, and put it in the
        output(property), which can be accessed 
        by another pipe.

        Some pipe subclasses may take some control
        of the process.
    """

    def __init__(self,
                previous_pipe, # // Subclass of self.
                process_task, 
                threshold_output:int, 
                verbosity:bool) -> None:
        """ 
            Init with properties:
                - previous_pipe: required but can be None.
                - process_task: the function hooked to self.process()
                    Must accept one value, return value will be appended
                    to self.output.
                - threshold_output: Max data count in self.output.
                    If this is exceeded, then some of the data
                    will be removed. Used to control memory usage.
                - verbosity: whether or not print is done or not 
                    (True might give _a_lot_ of information).
        """ 

        self.__process_task = process_task
        self.__threshold_output = threshold_output
        self.verbosity = verbosity

        self.previous_pipe = previous_pipe
        self.output = []


    def cond_print(self, msg):
        "Conditional printout, based on self.verbosity"
        if self.verbosity: 
            print(msg)

    def clear_overflow(self):
        "Clears output if it reaches self.__threshold_output"
        while len(self.output) > self.__threshold_output:
            self.output.pop(0)
            self.cond_print( "Length of output list reached"
                                ", removed oldest item.")


    def process(self):
        """ This method is meant to be called through
            subclasses. What it does:
        
            Process this pipe using a foreign method
            specified as 'process_task' in self.init.
        
            Attemts to move data from:
                self.previous_pipe.output
            .. to self.output.

            This method can be ignored if a subclass takes
            responsebility of moving the data.
        """
        # // Attempt move data.
        next_data = None
        if self.previous_pipe:
            if self.previous_pipe.output:
                next_data = self.previous_pipe.output.pop(0)
        processed_data = self.__process_task(next_data)
        # // Optional pass; output can be controlled by subclass.
        if processed_data: self.output.append(processed_data)
        # // Watch self.threshold_output.
        self.clear_overflow()
 