""" This primary function of this module is 
    to contain the 'Pipeline' class. See 
    docstring of that class for more information.
"""

class Pipeline():

    """ This class is a container for child classes of
        packages.pipes.collection.base.PipeBase.
        Activating this class with run() will
        start a loop which iterates over all contained
        pipes to process and pass their data. Monitor
        included.
    """

    def __init__(self, pipes:list) -> None:
        """ init with pipes, where pipes is a list of
            instances of pipe classes. Pipe classes
            are meant to be childs of 
            packages.pipes.collection.base.PipeBase.
        """
        self.pipes = pipes
        self.mon_line_length_highscore = 0# // Used for shell cleanup.


    def minitor_pipes(self) -> None:
        """ Writes a line in CLI to visualise
            the content of the pipes collected
            and processed with this class.
        """
        # // Construct string.
        padding_whitespace = 5
        mon_line = ""
        for n in range(len(self.pipes)):
            mon_line += self.pipes[n].__class__.__name__ + ": "
            mon_line += str(
                len(self.pipes[n].output)
                )  + " " *padding_whitespace
        # // Printout.
        print(
            f"{mon_line}{' '*self.mon_line_length_highscore}",
            end="\r", flush=True
        )
        # // Used to know exactly how much text to remove from shell.
        if self.mon_line_length_highscore < len(mon_line):
            self.mon_line_length_highscore = len(mon_line)


    def run(self) -> None:
        """ Starts a loop which iterates infinitely over
            all pipes contained in this class. Each iteration
            will call pipe.process() on each pipe. Monitor
            is called in this loop as well.
        """
        try:
            while True:
                for pipe in self.pipes:
                    pipe.process()
                self.minitor_pipes()
        except KeyboardInterrupt:
            pass
