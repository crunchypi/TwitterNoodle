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

from packages.pipes.pipeline import Pipeline


def get_pipe_feed_from_disk(filepath:str):
    """ Get an instance of 'FeedFromDiskPipe'
        with some general values. Requires a
        filepath to a dataset (pickled list of 
        tweepy tweets) and an output list reference.
    """
    return FeedFromDiskPipe(
            filepath=filepath,
            threshold_input=200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False
    )

def get_pipe_cleaning(previous_pipe):
    """ Get an instance of 'CleaningPipe' with
        some general values. Required an input
        and output list. For more info; see
        packages.pipes.collection.cleaning.
    """
    return CleaningPipe(
            previous_pipe=previous_pipe,
            threshold_input=200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False
    )

def get_pipe_simi(previous_pipe, recursion_level:int):
    """ Get an instance of 'SimiPipe' with
        some general values. Requires input
        and output list. 
        NOTE: This instance will load a 
        word2vec model and might require
        some time. For more information;
        see packages.pipes.collection.simi.
    """
    return SimiPipe(
            previous_pipe=previous_pipe,
            threshold_input=200, 
            threshold_output=200, 
            refreshed_data=False, 
            verbosity=False,
            recursion_level=recursion_level
    )

def get_pipe_feed_from_api(track:list):
    """ Get an instance of 'FeedFromAPIPipe' with
        some general values. Requires a 'track' list
        (of strings) which tells the Twitter API
        what to track and send back. Also requires
        an output list. For more information, see;
        packages.pipes.collection.feed_api.
    """
    return FeedFromAPIPipe(
        track=track,
        threshold_input=200,
        threshold_output=200,
        refreshed_data=True,
        verbosity=False
    )

def get_pipe_pyjs_bridge(previous_pipe, query:list = []):
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
        previous_pipe=previous_pipe,
        query=query,
        threshold_input=200,
        threshold_output=200,
        refreshed_data=True,
        verbosity=False
    )

def get_pipe_db(previous_pipe, start_fresh:bool=True):
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
        previous_pipe=previous_pipe,
        start_fresh=start_fresh,
        threshold_input=200,
        threshold_output=200,
        verbosity=False
    ) 


def get_pipeline_api_cln_simi_db(track_api:list = ["to", "and", "from"]):
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
    api_pipe = get_pipe_feed_from_api(
        track=track_api
    )
    cln_pipe = get_pipe_cleaning(
        previous_pipe=api_pipe
    )
    simi_pipe = get_pipe_simi(
        previous_pipe=cln_pipe,
        recursion_level=1
    )
    db_pipe = get_pipe_db(
        previous_pipe=simi_pipe,
        start_fresh=True
    )
    return Pipeline(
        pipes=[api_pipe, cln_pipe, simi_pipe, db_pipe]
    )


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
    dsk_pipe = get_pipe_feed_from_disk(
        filepath=filepath
    )
    cln_pipe = get_pipe_cleaning(
        previous_pipe=dsk_pipe
    )
    simi_pipe = get_pipe_simi(
        previous_pipe=cln_pipe,
        recursion_level=1
    )
    db_pipe = get_pipe_db(
        previous_pipe=simi_pipe,
        start_fresh=True
    )
    return Pipeline(
        pipes=[dsk_pipe, cln_pipe, simi_pipe, db_pipe]
    )

# @ not tested
def get_pipeline_dsk_cln_simi_js(filepath:str, initial_query:list):
    dsk_pipe = get_pipe_feed_from_disk(
        filepath=filepath
    )
    cln_pipe = get_pipe_cleaning(
        previous_pipe=dsk_pipe
    )
    simi_pipe = get_pipe_simi(
        previous_pipe=cln_pipe,
        recursion_level=1
    )
    bridge_pipe = get_pipe_pyjs_bridge(
        previous_pipe=simi_pipe,
        query=initial_query
    )
    return Pipeline(
        pipes=[dsk_pipe, cln_pipe, simi_pipe, bridge_pipe]
    )


def get_pipeline_api_cln_simi_js(
    apt_track:list = ["to", "and", "from"], 
    initial_query:list = ["python"]
    ):

    api_pipe = get_pipe_feed_from_api(
        track=apt_track
    )
    cln_pipe = get_pipe_cleaning(
        previous_pipe=api_pipe
    )
    simi_pipe = get_pipe_simi(
        previous_pipe=cln_pipe,
        recursion_level=1
    )
    bridge_pipe = get_pipe_pyjs_bridge(
        previous_pipe=simi_pipe,
        query=initial_query
    )
    return Pipeline(
        pipes=[api_pipe, cln_pipe, simi_pipe, bridge_pipe]
    )

