
class PipeBase():


    def __init__(self, 
                input: list,
                output: list,
                process_task, 
                threshold_input:int, 
                threshold_output:int, 
                refreshed_data:bool, 
                verbosity:bool) -> None:
        """"""

        self.__process_task = process_task
        self.__threshold_input = threshold_input
        self.__threshold_output = threshold_output
        self.__refreshed_data = refreshed_data
        self.verbosity = verbosity

        self.__input = input
        self.__output = output



    def cond_print(self, msg):
        if self.verbosity: 
            print(msg)


    # def push(self, data):
    #     if len(self.__input) < threshold_input:
    #         self.__input.push(data)
    #     else:
    #         self.cond_print("PipeBase/push: Input list full." + 
    #                          f"{'Doing Data shift.' if self.__refreshed_data else ''}")
    #         if self.__refreshed_data:
    #             self.__input.pop(0)
    #             self.__input.append(data)


    def process(self):
        if self.__input:
            oldest_data = self.__input.pop(0)
            self.cond_print(oldest_data)
            if oldest_data is not None: # Can be done
                processed_data = self.__process_task(oldest_data)
                # @ Have this as optional
                self.__output.append(processed_data)
            else:
                #self.cond_print("PipeBase/process: Recieved Nonetype data")
                pass # // deb