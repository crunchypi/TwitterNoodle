
class Pipeline():

    def __init__(self, pipes:list) -> None:
        self.pipes = pipes
        self.mon_line_length_highscore = 0# // Used for shell cleanup.


    def minitor_pipes(self) -> None:
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
        try:
            while True:
                for pipe in self.pipes:
                    pipe.process()
                self.minitor_pipes()
        except KeyboardInterrupt:
            pass
