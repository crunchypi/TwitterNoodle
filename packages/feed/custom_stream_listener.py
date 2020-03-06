from tweepy import StreamListener 


class CustomStreamListener(StreamListener):

    """ This is a subclass of a tweepy StreamListener
        which is a bare minimum for handing the listener.
        See tweepy documentation for more info.
    """

    def __init__(self, _destination:list, _stream_toggle:bool, _warn_verbosity:bool):
        """ Initialise with:
                - Bare-minimum requirements (call to super).
                - Conditional printout of warnings (_warn_verbosity).
                - A list where new tweets will go (_destination).
        """
        super(CustomStreamListener,self).__init__()
        self.destination = _destination
        self.stream_toggle = _stream_toggle
        self.warn_verbosity = _warn_verbosity

    def on_status(self, status):
        """ Tries to add new tweets to self.destination.
            This can be disabled with self.stream_toggle=False.
        """
        self.destination.append(status) if self.stream_toggle else self.out_warn("Stream OFF")

    def on_error(self, status_code):
        """ Tweepy error callback, only implementation is
            for rate limits, which automatically disables 
            streaming. Other warnings are printed out with
            conditional printing (self.out_warn).
        """
        # // 420 is the error code when a rate limit is reached
        if status_code == 420: 
            self.out_warn("Recieved rate limit warning, stopping stream")
            self.stream_toggle = False
            return False
        else:
            self.out_warn(f"misc error: {status_code}")

    def out_warn(self, msg):
        " Conditional printout "
        if self.warn_verbosity: print(msg)





