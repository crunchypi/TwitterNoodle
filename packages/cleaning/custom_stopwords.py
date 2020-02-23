from nltk.corpus import stopwords 

import_file = "packages/cleaning/custom_stopwords_list.txt"

collection = []

def file_to_list(path, out_list):
    with open(path, "r") as f:
        content = f.readline()
        while content:
            word = content.strip()
            out_list.append(word)
            content = f.readline()


def main():
    file_to_list(import_file, collection)
    stop_words = stopwords.words('english')
    collection.extend(stop_words)
    return set(collection)

