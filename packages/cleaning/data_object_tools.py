from packages.cleaning import data_object

""" This module contains some tools useful
    for handling DataObjects(packages.cleaning.data_object).
"""

def convert_tweet2dataobj(tweet): # -> DataObj
    """ Converts a tweepy tweet into a DataObj
        (packages.cleaning.data_object) and 
        returns that new instance.
    """
    new_obj = data_object.DataObj()
    new_obj.unique_id = tweet.id_str
    new_obj.name = tweet.user.name
    new_obj.text = tweet.text
    new_obj.coordinates = tweet.coordinates
    new_obj.place = tweet.place
    return new_obj


def siminet_to_txt(siminet:list, row_sep:str = "--", col_sep:str = "||") -> str:
    """ Converts a similarity net (see packages.similarity.process_tools),
        which is a 2d list, into a string. This is useful formatting
        to do if a similarity net is to be put into a database (Neo4j,
        specifically). Use txt_to_siminet, which is another function in
        this module, to convert back.
    """
    txt = ""
    for row in siminet:
        word = str(row[0])
        confidence = str(row[1])
        txt += f"{word}{col_sep}{confidence}{row_sep}"
        
    return txt


def txt_to_siminet(txt, row_sep:str = "--", col_sep:str = "||") -> list:
    """ Converts a string into a a similarity net (see 
        packages.similarity.process_tools), which is a 2d
        list. This can be useful for extracting similarity
        nets (string based) from a database(specifically Neo4j).
        Conversion the other way is done with siminet_to_txt,
        which is another function in this module.
    """
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