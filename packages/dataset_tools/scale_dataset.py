import os
import bz2
import pickle 

from packages.dataset_tools import common



def get_filenames_in_dir(path:str):
    " Gets all filenames in the input dir"
    file_names = [item[2] for item in os.walk(path)]
    undesirables = [".DS_Store"] # What to remove from file_names
    for x in undesirables:
        try:
            file_names[0].remove(x)
        except:
            pass  
    return file_names[0]


def get_file_content(filename):
    try: # // If zipped and pickled
        unzipped = bz2.BZ2File(filename).read()
        non_binary = pickle.loads(unzipped)
        return non_binary
    except: # // If only pickled
        try: # Attempt to read file
            with open(filename, "rb") as f:
                try: # // Attempt to unpickle
                    return pickle.load(f)
                except EOFError:
                    return None
        except FileNotFoundError:
            return None


def sort_tweetset_chronologically(tweet_list):
    tweet_list.sort(key=lambda tweet: tweet.created_at, reverse=False)


def merge_datasets_by_directory(input_dir, output_dir):
     # // Get all pickled lists.
    cache = []
    for name in get_filenames_in_dir(path=input_dir):
        # // Attempt to fetch content.
        content = get_file_content(f"{input_dir}{name}")
        if content:
            cache.extend(content)
    # // Sort and write new file
    if cache:
        sort_tweetset_chronologically(cache)
        common.save_data(
            content=cache,
            out_dir=output_dir,
            compressed=True
        )
    else:
        print("Did not merge dataset, check input and output files.")


def split_dataset_by_obj_count(divider:int, filename:str, out_dir:str):

    # // Get content and check it.
    cache_continious = get_file_content(filename=filename)
    if not cache_continious:
        print(f"Found no content in '{filename}'")
        return
    # // Sort for logical filaname ordering.
    sort_tweetset_chronologically(cache_continious)
    # // Temporary holder of content
    cache_chunked = []
    chunk_size = int(len(cache_continious) / divider)
    print(f"splitting: len: {len(cache_continious)}")#@
    while cache_continious:
        # // Transfer items between lists
        last_item = cache_continious.pop()
        cache_chunked.append(last_item)
        # // Save on chunksize
        if len(cache_chunked) >= chunk_size:
            # // Grab remainders, if any
            if len(cache_continious) < chunk_size:
                cache_chunked.extend(cache_continious)
            # // Save
            sort_tweetset_chronologically(cache_chunked)
            common.save_data(
                content=cache_chunked,
                out_dir=out_dir,
                compressed=True
            )
            cache_chunked.clear()
