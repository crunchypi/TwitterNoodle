import threading
import bz2
import pickle

""" This module contains some tools commonly used
    in the packages.dataset_tools file (where this
    module is located).
"""

def reformat_tweet_datetime(tweet) -> str:
    """ Reformat and return a timestamp
        attached to a tweet.
        Fromat: 
            YYMMDD-HH_MM(in)_SS.
        Example:
            200303-11_39_56
    """
    dt_string = str(tweet.created_at)
    dt_string = dt_string = dt_string[2:]
    dt_string = dt_string.replace("-", "")
    dt_string = dt_string.replace(" ", "-")
    dt_string = dt_string.replace(":", "_")
    return dt_string


def get_new_filename(cache:list, out_dir:str) -> str:
    """ Returns a filename which uses the range
        between the first and last tweet in the 'cache'.
        'cache' refers to a list of tweepy tweet objects.
        Example:
            'destination_dir/200303-11_39_54--200303-11_39_58'
    """
    filename_start = reformat_tweet_datetime(cache[0])
    filename_end = reformat_tweet_datetime(cache[-1])
    new_file_path = f"{out_dir}{filename_start}--{filename_end}"
    return new_file_path


def save_data(content:list, out_dir:str, compressed:bool, printout:bool = False) -> None:
    """ Saves some data with pickle and compression(optional).
        Uses threading, so is not blocking.
        Note: takes a copy of 'content' before the thread starts,
        so clearing the 'content' list is safe. 
    """
    # // Take a copy of content and get filename.
    content_copy = content.copy()
    filename = get_new_filename(
        cache=content_copy, 
        out_dir=out_dir
    )
    # // Saving closure for threaded run.
    def save():
        if compressed:
            sfile = bz2.BZ2File(f"{filename}.zip", 'w')
            pickle.dump(content_copy, sfile)
            sfile.close()
        else:
            pickle_out = open(filename, "wb")
            pickle.dump(content_copy, pickle_out)
            pickle_out.close()

        if printout: print(f"Saved to: '{filename}'")
    # // Create thread and run.
    save_thread = threading.Thread(target=save)
    save_thread.start()


