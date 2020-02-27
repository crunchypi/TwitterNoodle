from packages.pipes.base import PipeBase
from packages.pipes.cleaning import CleaningPipe
from packages.pipes.simi import SimiPipe
from packages.pipes.feed_disk import FeedFromDiskPipe

from packages.misc.custom_thread import CustomThread
from time import sleep


def setup_pipe_feed_from_disk(filepath, output):
    return FeedFromDiskPipe(
            filepath=filepath,
            output=output, 
            threshold_input = 200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False
    )

def setup_pipe_cleaning(input, output):
    return CleaningPipe(
            input=input,
            output=output, 
            threshold_input = 200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False
    )

def setup_pipe_simi(input, output):
    return SimiPipe(
            input=input,
            output=output,
            threshold_input = 200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False,
            recursion_level=1
    )
    
def setup_pipes(filepath:str = "../DataCollection/191120-21_34_19--191120-21_34_28") -> list:
    tweets = [] # // Collecting tweets
    cleaned_dataobjects = [] # // Cleaned dataobjects
    data_objects_simi = [] # // Dataobjects with siminets

    return [
        setup_pipe_feed_from_disk(filepath=filepath, output=tweets),
        setup_pipe_cleaning(input=tweets, output=cleaned_dataobjects),
        setup_pipe_simi(input=cleaned_dataobjects, output=data_objects_simi)
    ]



def run(forever:bool = False, runtime:int = 60):
    pipes = setup_pipes()

    def pipe_task():
        for pipe in pipes:
            pipe.process()
    try:
        pipe_thread = CustomThread(pipe_task, True) # @ details
        pipe_thread.start()
    except KeyboardInterrupt:
        pass

    while True:
        sleep(1)
        runtime -= 1
        if not forever and runtime <= 0:
            break

    # // Exit threads
    pipe_thread.is_looped = False