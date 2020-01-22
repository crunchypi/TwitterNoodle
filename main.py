import tweepy
#import asyncio
import time
import threading

from packages.feed.custom_stream_listener import CustomStreamListener as CSL
from packages.misc.custom_thread import CustomThread
from packages.feed.tweet_feed import Feed
from packages.cleaning import data_object
from packages.cleaning.basic_cleaner import BasicCleaner



run_for_seconds = 10
toggle_live = True
dataset_file_path = "../test_set"
track = ["how", "does", "one", "even", "go", "so", "far", "as", "to" ]
sentiment_range = [float(-1), float(-0.5)]

queue_stream = []
queue_cleaned = []

stream = None
listener = None



def setup_tweet_stream(out_stream):
    feed = Feed()
    if toggle_live:
        global listener 
        listener = feed.live_get_listener(out_stream)
        global stream 
        stream = feed.live_get_streamer(listener, track)
    else:
        global queue_stream
        queue_stream = feed.disk_get_tweet_queue(dataset_file_path)



def clean_process():
    tweet = queue_stream.pop(0)
    new_data_obj = data_object.get_dataobj_converted(tweet)
    BasicCleaner.autocleaner(new_data_obj, sentiment_range, True)
    queue_cleaned.append(new_data_obj)
    print(len(queue_stream))



switch_cleaner_loop = True # // AA: hack
def cleaner_loop():
    while switch_cleaner_loop:
        if len(queue_stream) > 0:
            clean_process()



setup_tweet_stream(queue_stream)

first_thread = CustomThread(cleaner_loop, False)
first_thread.start()

    

# // prevent immediate termination
while run_for_seconds > 0:
    run_for_seconds -= 1
    time.sleep(1)

switch_cleaner_loop = False
stream.disconnect() if stream is not None else ...
first_thread.stop()
print("terminating program")