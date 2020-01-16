# // Some tools related to the DataObj class

def siminet_compressed_to_txt(siminet, row_sep:str = "|rowsep|", col_sep:str = "|colsep|"):
    txt = ""
    for row in siminet:
        word = str(row[0])
        confidence = str(row[1])
        txt += f"{word}{col_sep}{confidence}{row_sep}"
    return txt

def txt_to_compressed_siminet(txt, row_sep:str = "|rowsep|", col_sep:str = "|colsep|"):
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