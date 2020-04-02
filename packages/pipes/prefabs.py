""" This file contains prefabs for different
    'pipelines' relevant to this system.
"""


from packages.pipes.collection.cleaning import CleaningPipe
from packages.pipes.collection.simi import SimiPipe
from packages.pipes.collection.feed_disk import FeedFromDiskPipe
from packages.pipes.collection.feed_api import FeedFromAPIPipe
from packages.pipes.collection.pyjs_bridge import PyJSBridgePipe
from packages.pipes.collection.database import DBPipe

from packages.pipes.pipeline import Pipeline



def get_pipeline_api_cln_simi_db(
        api_track:list = ["to", "and", "from", "but", "how", "why"],
        rec_lvl:int = 1,
        threshold_output:int = 200,
        verbosity:bool = False
    ):
    """ Gets a pipeline instance consisting of
            - FeedFromAPIPipe
            - CleaningPipe
            - SimiPipe
            - DBPipe
        The return is started with .run()

        Params:
            - api_track: What the Twitter API will track.
            - rec_lvl: Recursion lvl for SimiPipe(v2w).
            - threshold_output: Max data cap in each pipe.
            - verbosity: Whether or not pipes are verbose.

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
            recursion_level=rec_lvl
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
        rec_lvl:int = 1,
        threshold_output:int = 200,
        verbosity:bool = False
    ):
    """ Gets a pipeline instance consisting of
            - FeedFromDiskPipe
            - CleaningPipe
            - SimiPipe
            - DBPipe
        The return is started with .run()

        Params:
            - filepath: Path to input dataset.
            - rec_lvl: Recursion lvl for SimiPipe(v2w).
            - threshold_output: Max data cap in each pipe.
            - verbosity: Whether or not pipes are verbose.
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
            recursion_level=rec_lvl
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


def get_pipeline_dsk_cln_simi_js(
        filepath:str, 
        initial_query:list,
        rec_lvl:int = 1,
        threshold_output:int = 200,
        verbosity:bool = False
    ):
    """ Gets a pipeline instance consisting of
            - FeedFromDiskPipe
            - CleaningPipe
            - SimiPipe
            - PyJSBridgePipe
        The return is started with .run()

        Params:
            - filepath: Path to input dataset.
            - rec_lvl: Recursion lvl for SimiPipe(v2w).
            - initial_query: Words tracked by system.
            - threshold_output: Max data cap in each pipe.
            - verbosity: Whether or not pipes are verbose.
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
            recursion_level=rec_lvl
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
        api_track:list = ["to", "and", "from", "but", "how", "why"], 
        initial_query:list = ["python"],
        rec_lvl:int = 1,
        threshold_output:int = 200,
        verbosity:bool = False
    ):
    """ Gets a pipeline instance consisting of
            - FeedFromAPIPipe
            - CleaningPipe
            - SimiPipe
            - PyJSBridgePipe
        The return is started with .run()

        Params:
            - api_track: What the Twitter API will track.
            - initial_query: Words tracked by system.
            - threshold_output: Max data cap in each pipe.
            - verbosity: Whether or not pipes are verbose.
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
            recursion_level=rec_lvl
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

