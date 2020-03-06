# @ outdated: 030320
import matplotlib.pyplot as plt 
import pandas as pd 
import csv
from wordcloud import WordCloud 

from packages.feed.tweet_feed import Feed
from packages.cleaning.basic_cleaner import BasicCleaner
from packages.cleaning import data_object


""" This module provides some tools for doing exploratory data analysis.
    The user is expected to have read and understood this module before
    any usage, meaning that critical variables, such as 'file_path'
    should be set manually.
"""


# // Here for convinience.
file_path = "../datasplit/out/191120-21_34_19--191120-21_35_18" 
# // Acts globally, used in get_long_tweet_objects.
sentiment_range = [float(-1), float(1)]

def get_long_tweet_objects(path:str) -> list:
    """ Unpickles a local dataset (list of tweepy tweets),
        converts all tweets to dataobj(packages.cleaning.data_obj),
        cleans them with a cleaner (packages.cleaning.basic_cleaner)
        and returns a list of those dataobjects
    """
    feed = Feed()
    queue_stream = feed.disk_get_tweet_queue(path)
    data_objects = [data_object.get_dataobj_converted(tweet) for tweet in queue_stream]
    for obj in data_objects: BasicCleaner.autocleaner(obj,sentiment_range, False)
    return data_objects


def get_long_tweet_string(path):
    """ Uses local get_long_tweet_objects go get dataobjects and
        combine all their text fields into one single string,
        which is returned.
    """
    long_string = [obj.text*(obj.valid_sentiment_range) 
                    for obj in get_long_tweet_objects(path=path)]
    return " ".join(long_string)


def generate_wordcloud(path:str):
    """ Launch a rudimentary word cloud, using local 
        'get_long_tweet_string'.
    """

    word_cloud = WordCloud(
        width = 800, 
        height = 800, 
        background_color ='white',  
        min_font_size = 10
    ).generate(get_long_tweet_string(path=path)) 
    
    # plot word_cloud                       
    plt.figure(figsize = (8, 8), facecolor = None) 
    plt.imshow(word_cloud) 
    plt.axis("off") 
    plt.tight_layout(pad = 0) 
    plt.show() 


def write_csv(filename:str, dataobjects:list):
    """ Create a csv file with data from a list of
        dataobjects(packages.cleaning.data_object).

        Any exceptions raised while writing rows
        is ignored (a warn printout will occur).
    """
    with open(filename, 'w', newline='') as csvfile:
        obj_writer = csv.writer(csvfile, delimiter=',',
                                quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        # // Create header.
        obj_writer.writerow(
            ["name"] + 
            ["txt"] + 
            ["coord"] + 
            ["places"] + 
            ["hashtags"] + 
            ["alphatags"] + 
            ["sentiment"]
        )
        # // Write rows.
        for obj in dataobjects:
            try:
                obj_writer.writerow(
                    [obj.name] + 
                    [obj.text] + 
                    [obj.coordinates] +
                    [obj.place] + 
                    [obj.hashtags] +
                    [obj.alphatags] + 
                    [obj.valid_sentiment_range]
                )
            except:
                print("Exception warn: generate_wordcloud.write.csv")

