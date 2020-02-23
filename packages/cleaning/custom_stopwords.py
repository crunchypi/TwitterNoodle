from nltk.corpus import stopwords 

import_file = "packages/cleaning/custom_stopwords_list.txt"

l = []

def file_to_list(_in, _list):
    with open(_in, "r") as f:
        content = f.readline()
        while content:
            w = content.strip()
            _list.append(w)
            content = f.readline()


def main():
    file_to_list(import_file, l)
    stop_words = stopwords.words('english')
    l.extend(stop_words)
    return set(l)


