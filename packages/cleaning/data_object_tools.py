# // Some tools related to the DataObj class
from packages.cleaning import data_object


def convert_tweet2dataobj(tweet):
    new_obj = data_object.DataObj()
    new_obj.unique_id = tweet.id_str
    new_obj.name = tweet.user.name
    new_obj.text = tweet.text
    new_obj.coordinates = tweet.coordinates
    new_obj.place = tweet.place
    return new_obj


def siminet_to_txt(siminet, row_sep:str = "--", col_sep:str = "||"):
    txt = ""
    for row in siminet:
        word = str(row[0])
        confidence = str(row[1])
        txt += f"{word}{col_sep}{confidence}{row_sep}"
        
    return txt


def txt_to_siminet(txt, row_sep:str = "--", col_sep:str = "||"):
    siminet = []
    rows = txt.split(row_sep)
    for row in rows:
        columns = row.split(col_sep)
        # // check len because last is empty, caused by siminet_compressed_to_txt encoding
        if len(columns) >= 2: 
            # // failure/crash is an option, so not doing try&catch
            word = columns[0]
            confidence = float(columns[1])
            siminet.append([word, confidence])
                
    return siminet