import time
from datetime import datetime

from packages.dataset_tools import common
from packages.pipes.prefabs import get_pipe_feed_from_api
from packages.cleaning import custom_stopwords



class GenerateDataset():

    
    def __init__(self,  
                runtime_total:int=10, 
                runtime_between_slices:int=10, 
                runtime_forever:bool=False, 
                out_directory:str = "./", 
                track_keywords:list = custom_stopwords.main(),
                compression:bool = True):
        """ Creates an instance of the GenerateDataset class.
            Requires:
                - 'runtime_total' specifies the total runtime
                    of the data gathering.
                - 'runtime_between_slices' specifies how long
                    it will take between each save. If
                    this parameter = runtime_total, then only
                    one file will be created.
                - 'runtime_forever' will ignore 'runtime_total'
                - 'out_directory' is simply where the data will
                    be saved
                - 'track_keywords' is what the the Twitter API 
                    will send back. If this is left empty, then
                    only stopwords will be tracked.
                - 'compression'=True will compress all saved files.
        """
        self.runtime_total = runtime_total
        self.runtime_between_slices = runtime_between_slices
        self.runtime_forever = runtime_forever
        self.out_directory = out_directory
        self.track_keywords = track_keywords
        self.compression_enabled = compression


    def print_progress_bar(self, current ,max, bar_size = 20, descriptor="", leave_last=True):
        "A rudimentary progress bar, only meant for testing"
        # // Guard divide by zero
        percent = 0
        try: percent = float(current) / float(max) * float(100)
        except: pass
        # // Setup
        depict_arr = "="
        depict_empty = " "
        bar_progress = int((percent / 100 ) * bar_size)
        empty_count = int(bar_size - bar_progress)
        bar_str = f" |{depict_arr * bar_progress}>{depict_empty*empty_count}| {round(percent, 1)}%"
        print(f"{' '*100}", end="\r") # // Bad hack
        # // Execute
        if bar_progress is bar_size and leave_last: print(f"{descriptor} {bar_str}")
        else: print(f"{descriptor} {bar_str}", end="\r")


    def validate_session(self):
        "Checks if all necessary(for collection) properties are set."
        if self.runtime_total is None: return False
        if self.runtime_between_slices is None: return False
        if self.runtime_total % self.runtime_between_slices is not 0: return False
        if not self.runtime_forever and self.runtime_between_slices > self.runtime_total: return False
        if self.out_directory is None: return False
        if self.track_keywords is None: return False 
        
        return True


    def get_time_left(self):
        "Checks how many seconds remain before the collection task is complete."
        if self.runtime_forever: return "Undefined, running forever"
        if not self.validate_session(): return "session not valid"
        now = int(time.mktime(datetime.now().timetuple()))
        return self.runtime_total - (now - self.timestamp_start)


    def run_collector(self):
        """ Collects tweets and saves according to how the instance
            of this class was set up.
        """
        if not self.validate_session():
            print("session not valid, aborting")
            return

        # // Setup stream
        queue_stream = []
        feed_pipe = get_pipe_feed_from_api(
            track=self.track_keywords,
            output=queue_stream
        )

        # // Setup time, used for slicing sections of stream.
        time_current = int(time.mktime(datetime.now().timetuple()))
        self.timestamp_start = time_current
        time_end = time_current + self.runtime_total
        time_next_slice = time_current + self.runtime_between_slices

        # // Run
        while time_end > time_current or self.runtime_forever:
            time_current = int(time.mktime(datetime.now().timetuple()))
            feed_pipe.process()

            # // Save on slice
            if time_current >= time_next_slice :
                time_next_slice = time_current + self.runtime_between_slices
                common.save_data(
                    content=queue_stream, 
                    out_dir=self.out_directory, 
                    compressed=self.compression_enabled
                )
                queue_stream.clear()

            # // Display progresss
            self.print_progress_bar(
                current=(time_current - self.timestamp_start), 
                max=self.runtime_total,
                bar_size=20,  
                descriptor=f"time remaining: {self.get_time_left()}",
                leave_last=True
            )
                



def example(path="../DataCollection/", time_total=10, time_between_slices=5, track=None ):
    """ Example for how Generate_Dataset can be ran.
    """
    # // Setup and run.
    gen = GenerateDataset(
        runtime_total=time_total,
        runtime_between_slices=time_between_slices,
        runtime_forever= time_total < 0,
        out_directory=path,
        track_keywords=track
    )
    gen.run_collector()
    print("terminated")
