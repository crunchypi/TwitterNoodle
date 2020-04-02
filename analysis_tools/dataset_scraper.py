import os
import pickle
from random import randint

import os

#print(os.getcwd())

main_folder_prefix = "Data-"
sub_folder_prefix = "Sub-"
file_suffix = ".txt"
ignore = ["template-tweet.txt"]

topics = ["Art", "Food", "Incident", "IT", "Nature", "Sport"]

namefield_start = "<NAME>"
namefield_end = "</NAME>"
textfield_start = "<TEXT>"
textfield_end = "</TEXT>"




class sub(): # // Container for user, ment for Tweet
            def __init__(self):
                self.name = None

class Tweet(): # // Faux
    def __init__(self):
        self.id_str = None
        self.user = sub()
        self.text = None
        self.coordinates = None
        self.place = None




def get_substring(txt:str, start:str, end:str) -> str:
    txt = txt.split()
    index_start = 0
    index_end = 0
    for i in range(len(txt)):
        if start in txt[i]:
            index_start = i + 1
        if end in txt[i]:
            index_end = i
    return " ".join(txt[index_start:index_end])

def file2tweet(path:str, topic:str):
    new_tweet = Tweet()

    with open(path, "r") as f:
        content = f.read()
        if topic:
            new_tweet.user.name = topic
        else:
            new_tweet.user.name = get_substring(
                txt=content,
                start=namefield_start,
                end=namefield_end
            )
        new_tweet.text = get_substring(
            txt=content,
            start=textfield_start,
            end=textfield_end
        )
    return new_tweet

def check_duplicates(tweets:list):
    for x in tweets:
        for y in tweets:
            if x is not y:
                if x.user.name == y.user.name:
                    print(f"Duplicate name: {x.user.name}")
                if x.text == y.text:
                    print(f"Duplicate text: {x.text}")

def fetch_data_by_topic(path, topic):
    "Fetch "
    def crawler(current_path):
        names = os.listdir(current_path)
        collection = []
        for name in names:
            next_path = f"{current_path}/{name}"
            # // Dive into Data collections.
            if main_folder_prefix in name:
                res = crawler(current_path=next_path)
                if res: collection.extend(res)
            # // Dive into topics.
            if sub_folder_prefix in name:
                if topic in name:
                    res = crawler(current_path=next_path)
                    if res: collection.extend(res)
            # // Get tweets
            if file_suffix in name:
                if name not in ignore:
                    obj = file2tweet(
                        path=next_path, 
                        topic=topic
                    )
                    collection.append(obj)

        return collection

    return crawler(path)

def fetch_data_all(path:str, topics:list):
    "Fetch all data in path and return as list of tweets"
    collection = []
    for topic in topics:
        collection.extend(
            fetch_data_by_topic(path=path, topic=topic)
        )
    return collection


def assign_uid(tweets:list):
    "Assign unique user ids to all tweets"
    used_uids = []
    def get_id(used_uids):
        while True:
            new = randint(10000, 99999)
            if new not in used_uids:
                used_uids.append(new)
                return new

    for obj in tweets:
        obj.id_str = str(get_id(used_uids=used_uids))


def save(data, filename:str = "./analysis/data"):
    "save data as pickle"
    pickle_out = open(filename, "wb")
    pickle.dump(data, pickle_out)
    pickle_out.close()

def load(filename:str = "./analysis/data"):
    "load data from pickle"
    pickle_in = open(filename, "rb")
    data = pickle.load(pickle_in)
    pickle_in.close()
    return data



