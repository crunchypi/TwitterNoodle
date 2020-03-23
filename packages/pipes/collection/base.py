# // TODO:threshold handling?

class PipeBase():

    """ This class is meant to be a base class for 
        certain 'pipes' which are used to construct
        the 'pipelines' for this project.

        It includes input and output lists, which are 
        explicetly not encapsulated such that probing
        is easier (cost accepted).

        Thresholds(see init) are meant to indicate the
        maximum size of input and output lists. If these
        limits are exceeded, then one of two scenarios 
        will occur:
            1 - New data is dropped.
            2 - New data is added, but oldes is dropped.
        One of these two secarios will be determined by
        self.refresh_data (2 if True).

        Processing this pipe must be called manually with
        the method self.'process'.
    """

    def __init__(self,
                previous_pipe, # // Subclass of self.
                process_task, 
                threshold_output:int, 
                verbosity:bool) -> None:
        """ Initialise with required properties. See
            class docstring for more information.
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
            self.cond_print(
                "Length of output list reached, removed oldest item."
            )


    def process(self):
        """ Process this pipe with a method belonging to
            a subclass 'self.__process_task'. This subclass
            method can either:
                1 - Take new data, process and return it.
                    the processed data will go to self.output list.
                2 - Return nothing and handle data itself.
        """
        # // Attempt move data.
        next_data = None
        if self.previous_pipe:
            if self.previous_pipe.output:
                next_data = self.previous_pipe.output.pop(0)
        processed_data = self.__process_task(next_data)
        # // Optional pass; output can be controlled by subclass.
        if processed_data: self.output.append(processed_data)

        self.clear_overflow()
 