class DataObj():

    alphatags = []
    def __init__(self):
        self.unique_id = None
        self.name = None
        
        self.text = None
        self.coordinates = None
        self.place = None
        
        self.hashtags = []
        self.alphatags = []
        self.valid_sentiment_range = False

        self.siminet = [] # // compressed similarity net as in ProcessSimilarity class
