import threading
import bz2
import pickle

def reformat_tweet_datetime(tweet):
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

def get_new_filename(cache:list, out_dir) -> str:
    """ Returns a filename which uses the range
        between the first and last tweet in the 'cache'.
        Example:
            '200303-11_39_54--200303-11_39_58'
    """
    filename_start = reformat_tweet_datetime(cache[0])
    filename_end = reformat_tweet_datetime(cache[-1])
    new_file_path = f"{out_dir}{filename_start}--{filename_end}"
    return new_file_path

def save_data(content:list, out_dir:str, compressed:bool):
    """ Saves some data with pickle and compression(optional).
        Uses threading, so is not blocking.
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

        print(f"Saved to: {filename}")
    # // Create thread and run.
    save_thread = threading.Thread(target=save)
    save_thread.start()


