""" This file contains prefabs for the system.
        - Pipes (top-level interfaces for the system)
        - Pipelines (combinations of pipes)
    Pipes do different processes, such as cleaning 
    dataobjects(see packages.cleaning.data_object)
    
    Note: This file has a lot of repetition by design,
    this is meant to be a very simple top-level access
    point of the project.
"""

import threading

from packages.pipes.collection.cleaning import CleaningPipe
from packages.pipes.collection.simi import SimiPipe
from packages.pipes.collection.feed_disk import FeedFromDiskPipe
from packages.pipes.collection.feed_api import FeedFromAPIPipe
from packages.pipes.collection.pyjs_bridge import PyJSBridgePipe
from packages.pipes.collection.database import DBPipe




def get_pipe_feed_from_disk(filepath:str, output:list):
    """ Get an instance of 'FeedFromDiskPipe'
        with some general values. Requires a
        filepath to a dataset (pickled list of 
        tweepy tweets) and an output list reference.
    """
    return FeedFromDiskPipe(
            filepath=filepath,
            output=output, 
            threshold_input=200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False
    )

def get_pipe_cleaning(input:list, output:list):
    """ Get an instance of 'CleaningPipe' with
        some general values. Required an input
        and output list. For more info; see
        packages.pipes.collection.cleaning.
    """
    return CleaningPipe(
            input=input,
            output=output, 
            threshold_input=200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False
    )

def get_pipe_simi(input:list, output:list):
    """ Get an instance of 'SimiPipe' with
        some general values. Requires input
        and output list. 
        NOTE: This instance will load a 
        word2vec model and might require
        some time. For more information;
        see packages.pipes.collection.simi.
    """
    return SimiPipe(
            input=input,
            output=output,
            threshold_input=200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False,
            recursion_level=1
    )

def get_pipe_feed_from_api(track:list, output:list):
    """ Get an instance of 'FeedFromAPIPipe' with
        some general values. Requires a 'track' list
        (of strings) which tells the Twitter API
        what to track and send back. Also requires
        an output list. For more information, see;
        packages.pipes.collection.feed_api.
    """
    return FeedFromAPIPipe(
        track=track,
        output=output,
        threshold_input=200,
        threshold_output=200,
        refreshed_data=True,
        verbosity=False
    )

def get_pipe_pyjs_bridge(input:list, output:list, simitool, query:list = []):
    """ Get an instance of 'PyJSBridgePipe' with some general values.
        Requires an input and output list, and a simitool with a loaded 
        word2vec model (reccommended to borrow one from the pipe 
        created by get_pipe_simi() in this file). Also requires a 'query'
        list which must contain string(s). These strings will be 
        matched agains the objects in the input list (must be dataobjects)
        to get a similarity score. These float scores will be sent over
        websockets as soon as a connection is established.
        For more information:
            - get_pipe_simi (this file).
            - simitool (packages.similarity.process_tools).
            - dataobj (packages.cleaning.data_object).
        Examples of usage:
            - get_pipeline_dsk_cln_simi_js() (found in this file).
            - get_pipeline_api_cln_simi_js() (found in this file).
    """
    return PyJSBridgePipe(
        input=input,
        output=output,
        query=query,
        simitool=simitool,
        threshold_input=200,
        threshold_output=200,
        refreshed_data=True,
        verbosity=False
    )

def get_pipe_db(input:list, new_root_ring:bool=True):
    """ Get an instance of DBPipe with some general
        values. Requires an input list(expecting
        dataobjects with siminets) and an indicator
        (new_root_ring) for whether or not a new
        root ring is to be created. If there is no
        root ring, then one will be created anyway.
        for more information, see;
            - dataobj (packages.cleaning.data_object).
            - simipipe (packages.pipes.collection.simi).
            - DBPipe (packages.pipes.collection.database).
            - DB tools (packages.db.*).
    """
    return DBPipe(
        input=input,
        new_root_ring=new_root_ring,
        threshold_input=200,
        threshold_output=200,
        verbosity=False
    ) 


def get_pipeline_api_cln_simi_db(track_api:list = [" "]):
    """ Gets a pipeline consisting of;
            - FeedFromAPIPipe
            - CleaningPipe
            - SimiPipe
            - DBPipe
        The return is a function(closure) which
        uses two threads:
            1 - API.
            2 - For processing pipes.
        For more information, see;
        packages.pipes.collection.*
    """
    def procedure():
        tweets = []
        cleaned_dataobjects = []
        data_objects_simi = []

        # // Setup pipes and tie them together.
        pipe_tweets= get_pipe_feed_from_api(track=track_api, output=tweets)
        pipe_cleaned = get_pipe_cleaning(input=tweets, output=cleaned_dataobjects)
        pipe_simi = get_pipe_simi(input=cleaned_dataobjects, output=data_objects_simi)
        pipe_db = get_pipe_db(input=data_objects_simi)

        # // Task for processing pipes in continious loop.
        processing_pipes = [pipe_tweets, pipe_cleaned, pipe_simi, pipe_db]
        def process():
            while True:
                for pipe in processing_pipes:
                    pipe.process()

        # // Define and start thread.
        processing_thread = threading.Thread(target=process)
        processing_thread.start()

    return procedure


def get_pipeline_dsk_cln_simi_db(filepath:str): # @ Not tested.
    """ Gets a pipeline consisting of;
            - FeedFromAPIPipe
            - CleaningPipe
            - SimiPipe
            - DBPipe
        The return is a function(closure) which
        uses two threads:
            1 - API.
            2 - For processing pipes.
        For more information, see;
        packages.pipes.collection.*
    """
    def procedure():
        tweets = []
        cleaned_dataobjects = []
        data_objects_simi = []

        # // Setup pipes and tie them together.
        pipe_tweets = get_pipe_feed_from_disk(filepath=filepath, output=tweets)
        pipe_cleaned = get_pipe_cleaning(input=tweets, output=cleaned_dataobjects)
        pipe_simi = get_pipe_simi(input=cleaned_dataobjects, output=data_objects_simi)
        pipe_db = get_pipe_db(input=data_objects_simi)

        # // Task for processing pipes in continious loop.
        processing_pipes = [pipe_tweets, pipe_cleaned, pipe_simi, pipe_db]
        def process():
            while True:
                for pipe in processing_pipes:
                    pipe.process()

        # // Define and start thread.
        processing_thread = threading.Thread(target=process)
        processing_thread.start()

    return procedure


def get_pipeline_dsk_cln_simi_js(
        monitor_hook = lambda: None,
        filepath:str = "../DataCollection/191120-21_34_19--191120-21_34_28", 
        ):
    """ Gets a pipeline consisting of;
            - FeedFromDiskPipe
            - CleaningPipe
            - SimiPipe
            - PyJSBridgePipe
        The return is a function(closure) which
        uses two threads:
            1 - For processing pipes (excluding PyJSBridge).
            2 - For PyJSBridge (also uses asyncio).
        For more information, see;
        packages.pipes.collection.*
    """
    if not callable(monitor_hook): raise ValueError("Expected function.")
    def procedure(): 
        tweets = [] # // Collecting tweets
        cleaned_dataobjects = [] # // Cleaned dataobjects
        data_objects_simi = [] # // Dataobjects with siminets
        scores = []

        # // Setup pipes and tie them together.
        pipe_tweets = get_pipe_feed_from_disk(filepath=filepath, output=tweets)
        pipe_cleaned = get_pipe_cleaning(input=tweets, output=cleaned_dataobjects)
        pipe_simi = get_pipe_simi(input=cleaned_dataobjects, output=data_objects_simi)
        pipe_js = get_pipe_pyjs_bridge(
            query=["cat", "car", "home"], 
            simitool=pipe_simi.simitool,
            input=data_objects_simi,
            output=scores
        )

        # // Task for processing regular pipes.
        # // Excluding pipe_js because it has to be ran on a sep thread.
        processing_pipes = [pipe_tweets, pipe_cleaned, pipe_simi]
        def process():
            while True:
                for pipe in processing_pipes:
                    pipe.process()

        processing_thread = threading.Thread(target=process)
        monitor_thread = threading.Thread(target=monitor_hook)

        try:
            processing_thread.start()   # Thread for pipeline.
            monitor_thread.start()      # Thread for monitor hook.
            pipe_js.start()             # Thread for network.
        except KeyboardInterrupt:
            processing_thread.stop()
            monitor_thread.stop()
            pipe_js.stop()

    return procedure


def get_pipeline_api_cln_simi_js(
        monitor_hook = lambda: None,
        track_api:list = [" "], 
        track_incident:list = [" "]
        ):
    """ Gets a pipeline consisting of;
            - FeedFromAPIPipe
            - CleaningPipe
            - SimiPipe
            - PyJSBridgePipe
        The return is a function(closure) which
        uses three threads:
            1 - API.
            2 - For processing pipes (excluding PyJSBridge).
            3 - PyJSBrdige (which also uses asyncio).
        For more information, see;
        packages.pipes.collection.*
    """
    if not callable(monitor_hook): raise ValueError("Expected function.")
    if type(track_api) is not list: raise ValueError("Expected list")
    if type(track_incident) is not list: raise ValueError("Expected list")

    def validate_tracks(track, errormsg):
        for item in track:
            if type(item) is not str: raise ValueError(errormsg)

    validate_tracks(track=track_api, errormsg="Found non-alpha in 'track_api'")
    validate_tracks(track=track_incident, errormsg="Found non-alpha in 'track_incident'")

    def procedure(): 
        tweets = [] # // Collecting tweets
        cleaned_dataobjects = [] # // Cleaned dataobjects
        data_objects_simi = [] # // Dataobjects with siminets
        scores = []

        # // Setup pipes and tie them together.
        pipe_tweets = get_pipe_feed_from_api(track=track_api, output=tweets)
        pipe_cleaned = get_pipe_cleaning(input=tweets, output=cleaned_dataobjects)
        pipe_simi = get_pipe_simi(input=cleaned_dataobjects, output=data_objects_simi)
        pipe_js = get_pipe_pyjs_bridge(
            query=track_incident, 
            simitool=pipe_simi.simitool,
            input=data_objects_simi,
            output=scores
        )

        # // Task for processing regular pipes.
        # // Excluding pipe_js because it has to be ran on a sep thread.
        processing_pipes = [pipe_tweets, pipe_cleaned, pipe_simi]
        def process():
            while True:
                for pipe in processing_pipes:
                    pipe.process()

        def monitor():
            while True:
                tweets_deb = f"Tweets: {len(tweets)}"
                cleaned_deb = f"Cleaned: {len(cleaned_dataobjects)}"
                simi_deb = f"With Simi: {len(data_objects_simi)}"
                js_deb = f"JS: {len(scores)}"
                print(f"{tweets_deb} | {cleaned_deb} | {simi_deb} | {js_deb}", end="\r")

        monitor_hook = monitor

        processing_thread = threading.Thread(target=process)
        monitor_thread = threading.Thread(target=monitor_hook)

        try:
            processing_thread.start()   # Thread for pipeline.
            monitor_thread.start()      # Thread for monitor hook.
            pipe_js.start()             # Thread for network.
        except KeyboardInterrupt:
            processing_thread.stop()
            monitor_thread.stop()
            pipe_js.stop()

    return procedure

