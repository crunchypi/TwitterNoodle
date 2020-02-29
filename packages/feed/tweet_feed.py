import tweepy
import pickle
from packages.feed.custom_stream_listener import CustomStreamListener as CSL
import credentials

class Feed():

    def __init__(self):
            self.auth = credentials.auth
            self.api = tweepy.API(self.auth)
            self.api.wait_on_rate_limit = True
            self.api.wait_on_rate_limit_notify = True

    def live_get_listener(self, queue_stream):
        listener = CSL(_destination = queue_stream,
                                    _stream_toggle = True,
                                        _warn_verbosity = True)
        return listener

    def live_get_streamer(self, listener, track):
        stream = tweepy.Stream(auth = self.auth, listener=listener)
        stream.filter(track=track, languages=["en"], is_async= True)
        return stream

    # returns a chunk list, should consider using a generator
    def disk_get_tweet_queue(self, file_path):
        try:
            pickle_in = open(file_path, "rb")
            data = pickle.load(pickle_in)
            pickle_in.close()
            return data
        except:
            print("warn: could not get tweet queue from file_path")
