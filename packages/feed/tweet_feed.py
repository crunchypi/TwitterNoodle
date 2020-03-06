import tweepy
import pickle
from packages.feed.custom_stream_listener import CustomStreamListener as CSL
import credentials

class Feed():

    """ This class is responsible for getting tweets, either
        from tweepy and CustomStreamListener
            (packages.feed.custom_stream_listener)
        .. or from a dataset already stored on the machine,
        which should be a pickle with a list of tweepy
        tweet objects (Note: compressed pickles is not supported).
    """

    def __init__(self):
        """ Sets up properties for live listener (tweepy),
            requires relevant credentials to be set in the 
            root folder (credentials.py).
        """
        self.auth = credentials.auth
        self.api = tweepy.API(self.auth)
        self.api.wait_on_rate_limit = True
        self.api.wait_on_rate_limit_notify = True

    def live_get_listener(self, queue_stream):
        " Sets up CustomStramListener returns it. "
        listener = CSL(_destination = queue_stream,
                                    _stream_toggle = True,
                                        _warn_verbosity = True)
        return listener

    def live_get_streamer(self, listener, track):
        " Sets up tweepy.Stream and returns it. "
        stream = tweepy.Stream(auth = self.auth, listener=listener)
        stream.filter(track=track, languages=["en"], is_async= True)
        return stream

    def disk_get_tweet_queue(self, file_path):
        """ Returns a pickled dataset. should be list of tweepy tweets. 
            Does it in one single batch.

            Failure is allowed to crash, so incorrect file_path
            is not the responsebility of this method.
        """
        pickle_in = open(file_path, "rb")
        data = pickle.load(pickle_in)
        pickle_in.close()
        return data

