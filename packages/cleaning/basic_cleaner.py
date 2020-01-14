
#from nltk.corpus import stopwords  # // AA(071119): deprecated
import re
import string
from textblob import TextBlob as TB

import packages.cleaning.custom_stopwords as custom_stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer 





class BasicCleaner():



    @staticmethod
    def print_comparison(_data_obj, _text_raw:str) -> None:
        try:
            print("##########################")
            print("-------start raw----------")
            print(_text_raw)
            print("--------end raw-----------")
            print("-------start new----------")
            print(_data_obj.text)
            print(f"sentiment:{_data_obj.valid_sentiment_range}")
            print(f"hashtags: {_data_obj.hashtags}")
            print(f"alphatags:{_data_obj.alphatags}")
            print("--------end new-----------")
            print("##########################")
        except:
            pass

    @classmethod
    def autocleaner(self, _data_obj, _sentiment_range:float, _verbosity:bool) -> None:

        text_raw = _data_obj.text

        _data_obj.text = self.clean_links(_data_obj.text)

        # // Filter alphatags
        filtered_alphatags = self.clean_alphatags(_data_obj.text)
        _data_obj.text = filtered_alphatags[0]
        _data_obj.alphatags = filtered_alphatags[1]
 
        # // Filter hashtags
        filtered_hashtags = self.clean_hashtags(_data_obj.text)
        _data_obj.text = filtered_hashtags[0]
        _data_obj.hashtags = filtered_hashtags[1]

        # // Clean a lot of shit
        _data_obj.text = self.clean_convert_to_lowercase(_data_obj.text)
        #print(f'type: {type(_data_obj.text)}  {_data_obj.text}')
        #_data_obj.text = self.tokenise(_data_obj.text)
        _data_obj.text = self.clean_stopwords(_data_obj.text)
        #_data_obj.text = self.detokenise(_data_obj.text)
        _data_obj.text = self.clean_punctuation(_data_obj.text)
        _data_obj.text = self.remove_duplica_words(_data_obj.text)
        _data_obj.valid_sentiment_range = self.set_sentiment(
                                               _data_obj.text,
                                               _sentiment_range
                                               )

        if _verbosity:
            self.print_comparison(_data_obj, text_raw)

    @staticmethod
    def remove_duplica_words(content:str) -> str:
        words = content.split()
        non_dup = set(words)
        return " ".join(non_dup)

 
    @staticmethod
    def tokenise(content):
        return word_tokenize(content)

    @staticmethod
    def detokenise(content):
        return TreebankWordDetokenizer().detokenize(content)

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
        # Removed on 010120.
        #_data_obj.text = _data_obj.text.translate(str.maketrans('', '', string.punctuation))
        # Added on 010120 for testing, will revert by 010220 if it's bust.
        new_string = ""
        str_split = content.split()
        for chunk in str_split:
            tmp = ""
            for char in chunk:
                if char.isalpha():
                    tmp += char
            new_string += f" {tmp}" # // could check if tmp only contains space
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