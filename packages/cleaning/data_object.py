class DataObjStateEnum():
    def __init__(self):
        pass # // AA: not implemented

class DataObj():

    alphatags = []
    def __init__(self):
        self.unique_id = None
        self.name = None
        #self.handle = None
        self.text = None
        self.coordinates = None
        self.place = None
        #self.id = None
        self.hashtags = []
        self.alphatags = []
        self.valid_sentiment_range = False

        self.siminet_compressed = [] # // compressed similarity net as in ProcessSimilarity class

        # // AA: Twitter obj entities might be worth looking into

        self.possible_states = None # // AA: not implemented
        self.state = "Empty"


def get_dataobj_converted(tweet):
    new_obj = DataObj()
    new_obj.unique_id = tweet.id_str
    new_obj.name = tweet.user.name
    new_obj.text = tweet.text
    new_obj.coordinates = tweet.coordinates
    new_obj.place = tweet.place
    return new_obj


