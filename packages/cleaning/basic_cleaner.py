a
#from nltk.corpus import stopwords  # // AA(071119): deprecated
import re
import string
from textblob import TextBlob as TB

import packages.cleaning.custom_stopwords as custom_stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer 



class BasicCleaner():

    """ This is a static class meant to contain 'cleaning' methods.
        'Cleaning' in this context refers to preparing various strings
        for ML processing.
    """

    @staticmethod
    def print_comparison(data_obj, text_raw:str) -> None:
        """ This method is meant for debugging; mainly
            displaying a DataObject(packages.cleaning.data_object)
            and comparing non-cleaned and cleaned text.
        """
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
        """ This method is specific for the project at large; taking in a 
            DataObject(packages.cleaning.data_object) and reducing the 
            'text' field by removing punctuation, stop-words, etc.
            Note: in-place processing. 
        """

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
        # // Clean name (db safety).
        data_obj.name = self.clean_punctuation(data_obj.name)

        if verbosity:
            self.print_comparison(data_obj, text_raw)


    @staticmethod
    def remove_duplica_words(content:str) -> str:
        """ Removing duplicate words in a string
            before returning it back.
        """ 
        words = content.split()
        non_dup = set(words)
        return " ".join(non_dup)


    @staticmethod
    def clean_stopwords(content:str) -> str:
        """ This method removes stop-words from
            a string before returning it back.
        """
        content = content.split()
        filtered = [item for item in content
                    if not item in custom_stopwords.main()]
        return ' '.join(filtered)


    @staticmethod
    def clean_punctuation(content:str) -> str:
        """ This method removes punctuation AND
            numbers (leaving only alpha), from 
            a string before returning it back.
        """
        new_string = ""
        str_split = content.split()
        for chunk in str_split:
            tmp = ""
            for char in chunk:
                if char.isalpha():
                    tmp += char
            if len(tmp) > 0:
                new_string += f" {tmp}" # // could check if tmp only contains space.
        return new_string


    @staticmethod
    def clean_links(content:str) -> str:
        """ This method removes all percieved
            links from a string before returning
            it back. This is not fool-proof.
        """
        links = re.sub(r"[a-z]*[:.]+\S+","",content)
        return links


    @staticmethod
    def clean_hashtags(content:str) -> list:
        """ This method takes in a string and
            filters out words with a hashtag
            in front of it. Returns a list 
            which contains a new string (with
            hashtag removed) and a string with
            the hashtag word. 
            Example:
                "The #Zen of Python" ->
                    ["The of Python", "#Zen"]
        """
        hashtag = (re.findall(r"[#]\S*", content))
        text = re.sub(r"[#]\S*", "", content)
        return [text, hashtag]


    @staticmethod
    def clean_alphatags(content:str) -> list:
        """ This method takes in a string and
            filters out words with an alphatag
            in front of it. Returns a list
            which contains a new string (with
            alphatag removed) and a string with
            the alphatag word.
            Example:
                "@tetris life" ->
                    ["life", "@tetris]
        """
        alphatag = (re.findall(r"[@]\S*", content))
        text = re.sub(r"[@]\S*", "", content)
        return [text, alphatag]


    @staticmethod
    def clean_convert_to_lowercase(content:str) -> str:
        """ Takes in a string and makes all characters
            lower-case before returning it back. Simply
            a stand-in for str.lower() which can be
            expanded in the future.
        """
        return content.lower()


    @staticmethod
    def set_sentiment(content:str, range:list) -> bool:
        """ Uses textblob to guauge if some content is
            within a sentiment range. 'range' must be
            in this form: [float(lower), float(upper)].
            The minmax is: Min(-1.0), Max(1.0). 
            Example: 
                Profanity tends to be somewhere between
                -1.0 and 0.0
            Returns a True if the 'content' is within
            the specified range, else false.
        """
        score = TB(content).sentiment[0]
        return (score >= range[0]) and (score <= range[1])