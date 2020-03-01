



def connect_pipes(pipes:list, entry:list = [], exit:list = []):
    last = entry
    for pipe in pipes:
        pipe.input = last

        if pipe is pipes[-1]:
            pipe.output = exit
        else:
            next_last = []
            pipe.output = next_last

    return (entry, exit)

def setup_pipes_dsk_cln_simi(filepath:str = "../DataCollection/191120-21_34_19--191120-21_34_28") -> list:



def setup_pipes(filepath:str = "../DataCollection/191120-21_34_19--191120-21_34_28") -> list:
    #tweets = [] # // Collecting tweets
    #cleaned_dataobjects = [] # // Cleaned dataobjects
    #data_objects_simi = [] # // Dataobjects with siminets


    pipes = [
        prefabs.setup_pipe_feed_from_disk(filepath=filepath, output=tweets),
        prefabs.setup_pipe_cleaning(input=tweets, output=cleaned_dataobjects),
        prefabs.setup_pipe_simi(input=cleaned_dataobjects, output=data_objects_simi)
    ]
    