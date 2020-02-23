
#from nltk.corpus import stopwords  # // AA(071119): deprecated
import re
import string
from textblob import TextBlob as TB

import packages.cleaning.custom_stopwords as custom_stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer 





class BasicCleaner():



    @staticmethod
    def print_comparison(data_obj, text_raw:str) -> None:
        try:
            print("##########################")
            print("-------start raw----------")
            print(text_raw)
            print("--------end raw-----------")
            print("-------start new----------")
            print(data_obj.text)
            print(f"sentiment:{data_obj.valid_sentiment_range}")
            print(f"hashtags: {data_obj.hashtags}")
            print(f"alphatags:{data_obj.alphatags}")
            print("--------end new-----------")
            print("##########################")
        except:
            pass

    @classmethod
    def autocleaner(self, data_obj, sentiment_range:float, verbosity:bool) -> None:

        text_raw = data_obj.text

        data_obj.text = self.clean_links(data_obj.text)

        # // Filter alphatags.
        filtered_alphatags = self.clean_alphatags(data_obj.text)
        data_obj.text = filtered_alphatags[0]
        data_obj.alphatags = filtered_alphatags[1]
 
        # // Filter hashtags.
        filtered_hashtags = self.clean_hashtags(data_obj.text)
        data_obj.text = filtered_hashtags[0]
        data_obj.hashtags = filtered_hashtags[1]

        # // Additional cleaning.
        data_obj.text = self.clean_convert_to_lowercase(data_obj.text)
        data_obj.text = self.clean_stopwords(data_obj.text)
        data_obj.text = self.clean_punctuation(data_obj.text)
        data_obj.text = self.remove_duplica_words(data_obj.text)
        data_obj.valid_sentiment_range = self.set_sentiment(
                                               data_obj.text,
                                               sentiment_range
                                        )

        if verbosity:
            self.print_comparison(data_obj, text_raw)

    @staticmethod
    def remove_duplica_words(content:str) -> str:
        words = content.split()
        non_dup = set(words)
        return " ".join(non_dup)

    @staticmethod
    def clean_dates(content:str) -> str:
        pass

    @staticmethod
    def clean_stopwords(content:str) -> str:
        content = content.split()
        filtered = [item for item in content
                    if not item in custom_stopwords.main()]
        return ' '.join(filtered)

    @staticmethod
    def clean_punctuation(content:str) -> str:
        new_string = ""
        str_split = content.split()
        for chunk in str_split:
            tmp = ""
            for char in chunk:
                if char.isalpha():
                    tmp += char
            new_string += f" {tmp}" # // could check if tmp only contains space.
        return new_string

    @staticmethod
    def clean_links(content:str) -> str:
        links = re.sub(r"[a-z]*[:.]+\S+","",content)
        return links

    @staticmethod
    def clean_hashtags(content:str) -> list:
        hashtag = (re.findall(r"[#]\S*", content))
        text = re.sub(r"[#]\S*", "", content)
        return [text, hashtag]

    @staticmethod
    def clean_alphatags(content:str) -> list:
        alphatag = (re.findall(r"[@]\S*", content))
        text = re.sub(r"[@]\S*", "", content)
        return [text, alphatag]

    @staticmethod
    def clean_convert_to_lowercase(content:str) -> str:
        return content.lower()

    @staticmethod
    def set_sentiment(content:str, range:float) -> bool:
        score = TB(content).sentiment[0]
        return (score >= range[0]) and (score <= range[1])