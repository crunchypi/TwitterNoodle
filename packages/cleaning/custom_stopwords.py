from nltk.corpus import stopwords 

""" A minimalistic module which combines custom 
    stopwords with nltk.corpus.stopwords
"""

import_file = "packages/cleaning/custom_stopwords_list.txt"

__collection = []

def __file_to_list(path:str, out_list:list) -> None:
    """ Simply open a file and import words
        listed (one word per line), strips 
        new-line character and puts content
        into a 'out_list'.
    """
    with open(path, "r") as f:
        content = f.readline()
        while content:
            word = content.strip()
            out_list.append(word)
            content = f.readline()


def main() -> set:
    """ Combines custom stop-words with
        stopwords from nltk.corpus.stopwords,
        before returning a set (no duplicates).
    """
    __file_to_list(import_file, __collection)
    stop_words = stopwords.words('english')
    __collection.extend(stop_words)
    return set(__collection)

