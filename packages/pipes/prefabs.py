""" This file contains prefabs for the system.
        - Pipes (top-level interfaces for the system)
        - Pipelines (combinations of pipes)
    Pipes do different processes, such as cleaning 
    dataobjects(see packages.cleaning.data_object)
    
    Note: This file has a lot of repetition by design,
    this is meant to be a very simple top-level access
    point of the project.
"""


from packages.pipes.collection.cleaning import CleaningPipe
from packages.pipes.collection.simi import SimiPipe
from packages.pipes.collection.feed_disk import FeedFromDiskPipe
from packages.pipes.collection.feed_api import FeedFromAPIPipe
from packages.pipes.collection.pyjs_bridge import PyJSBridgePipe
from packages.pipes.collection.database import DBPipe

from packages.pipes.pipeline import Pipeline



def get_pipeline_api_cln_simi_db(
        api_track:list = ["to", "and", "from"],
        threshold_output:int = 200,
        verbosity:bool = False
    ):
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
    api_pipe = FeedFromAPIPipe(
        track=api_track,
        threshold_output=threshold_output,
        verbosity=verbosity
    )
    cln_pipe = CleaningPipe(
            previous_pipe=api_pipe,
            threshold_output=threshold_output,
            verbosity=verbosity
    )
    simi_pipe = SimiPipe(
            previous_pipe=cln_pipe,
            threshold_output=threshold_output,
            verbosity=verbosity,
            recursion_level=1 # @ make global
    )
    db_pipe = DBPipe(
        previous_pipe=simi_pipe,
        start_fresh=True,
        threshold_output=threshold_output,
        verbosity=verbosity
    )
    return Pipeline(
        pipes=[api_pipe, cln_pipe, simi_pipe, db_pipe]
    )


def get_pipeline_dsk_cln_simi_db(
        filepath:str,
        threshold_output:int = 200,
        verbosity:bool = False
    ): # @ Not tested.
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
    dsk_pipe = FeedFromDiskPipe(
            filepath=filepath,
            threshold_output=threshold_output,
            verbosity=verbosity
    )
    cln_pipe = CleaningPipe(
            previous_pipe=dsk_pipe,
            threshold_output=threshold_output,
            verbosity=verbosity
    )
    simi_pipe = SimiPipe(
            previous_pipe=cln_pipe,
            threshold_output=threshold_output,
            verbosity=verbosity,
            recursion_level=1 # @ make global
    )
    db_pipe = DBPipe(
        previous_pipe=simi_pipe,
        start_fresh=True,
        threshold_output=threshold_output,
        verbosity=verbosity
    )
    return Pipeline(
        pipes=[dsk_pipe, cln_pipe, simi_pipe, db_pipe]
    )

# @ not tested
def get_pipeline_dsk_cln_simi_js(
        filepath:str, 
        initial_query:list,
        threshold_output:int = 200,
        verbosity:bool = False
    ):
    dsk_pipe = FeedFromDiskPipe(
            filepath=filepath,
            threshold_output=threshold_output, 
            verbosity=verbosity
    )
    cln_pipe = CleaningPipe(
            previous_pipe=dsk_pipe,
            threshold_output=threshold_output,
            verbosity=verbosity
    )
    simi_pipe = SimiPipe(
            previous_pipe=cln_pipe,
            threshold_output=threshold_output,
            verbosity=verbosity,
            recursion_level=1
    )
    bridge_pipe = PyJSBridgePipe(
        previous_pipe=simi_pipe,
        query=initial_query,
        threshold_output=threshold_output,
        verbosity=verbosity
    )
    return Pipeline(
        pipes=[dsk_pipe, cln_pipe, simi_pipe, bridge_pipe]
    )


def get_pipeline_api_cln_simi_js(
        api_track:list = ["to", "and", "from"], 
        initial_query:list = ["python"],
        threshold_output:int = 200,
        verbosity:bool = False
    ):

    api_pipe = FeedFromAPIPipe(
        track=api_track,
        threshold_output=threshold_output,
        verbosity=verbosity
    )
    cln_pipe = CleaningPipe(
            previous_pipe=api_pipe,
            threshold_output=threshold_output,
            verbosity=verbosity
    )
    simi_pipe = SimiPipe(
            previous_pipe=cln_pipe,
            threshold_output=threshold_output,
            verbosity=verbosity,
            recursion_level=1 # @ make global
    )
    bridge_pipe = PyJSBridgePipe(
        previous_pipe=simi_pipe,
        query=initial_query,
        threshold_output=threshold_output,
        verbosity=verbosity
    )
    return Pipeline(
        pipes=[api_pipe, cln_pipe, simi_pipe, bridge_pipe]
    )

