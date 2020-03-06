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
                input: list,
                output: list,
                process_task, 
                threshold_input:int, 
                threshold_output:int, 
                refreshed_data:bool, 
                verbosity:bool) -> None:
        """ Initialise with required properties. See
            class docstring for more information.
        """ 

        self.__process_task = process_task
        self.__threshold_input = threshold_input
        self.__threshold_output = threshold_output
        self.__refreshed_data = refreshed_data
        self.verbosity = verbosity

        self.input = input
        self.output = output


    def cond_print(self, msg):
        "Conditional printout, based on self.verbosity"
        if self.verbosity: 
            print(msg)


    def process(self):
        """ Process this pipe with a method belonging to
            a subclass 'self.__process_task'. This subclass
            method can either:
                1 - Take new data, process and return it.
                    the processed data will go to self.output list.
                2 - Return nothing and handle data itself.
        """
        # // Fetch oldest data from self.input[0].
        if self.input:
            oldest_data = self.input.pop(0)
            self.cond_print(oldest_data)
            # // Validate not None and process.
            if oldest_data is not None:
                processed_data = self.__process_task(oldest_data)
                # // Optional pass, determined by implementation of subclasses.
                if processed_data: self.output.append(processed_data)
 