class DataObj():

    """ This class is meant to be a container of 
        tweet data for the TwitterNoodle project.
        It is passed along most of the system.
    """

    def __init__(self):
        """ Initialises an emty DataObj with
            some useful fields. Values are 
            either None, False or [].
        """
        self.unique_id = None
        self.name = None
        
        self.text = None
        self.coordinates = None
        self.place = None
        
        self.hashtags = []
        self.alphatags = []
        self.valid_sentiment_range = False

        # // Note: siminet is created in packages.similarity.process_tools.
        self.siminet = []
