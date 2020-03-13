""" A very rudimentary query interface.
"""

from packages.db.db_mana import DBMana
from packages.similarity.process_tools import ProcessSimilarity

def get_db_tool():
    "Setup and return of dbtools (with simitool)"
    print("Doing setup..")
    db_tool = DBMana()
    db_tool.setup_db_tools()
    db_tool.setup_db_tools()

    # // For query->siminet conversion.
    simitool = ProcessSimilarity()
    simitool.load_model()
    db_tool.simitool = simitool

    print("Setup done.")
    return db_tool

def set_query(previous:list, db_tool):
    """ Updates 'previous' query item. Requires
        a 'db_tool' with simitool (loaded model).
    """
    print(f"Last query: '{previous[0]}'")
    query = input(("Type in query (separate with space)"
                    " and press enter. Leave empty to skip:\n"))

    if query:
        previous[0] = query
        separated = query.split()
        previous[1] = db_tool.simitool.get_similarity_net(
            query=separated
        )

def display_data(dataobjects:list):
    """ Prints out a list of dataobjects. 
        Data used:
            - Name/handle
            - Text(cleaned)
        Text formatted.
    """
    print(f"{'-'*10}")

    # // Formatting.
    padding = 1
    handlespace = 0
    for item in dataobjects:
        if len(item.name) > handlespace:
            handlespace = len(item.name) + padding

    # // Printout.
    for item in dataobjects:
        wspace_count = handlespace - len(item.name)
        print(
            f"Handle: '{item.name}'{wspace_count*' '}| text: {item.text}"
        )
    print(f"{'-'*10}")

def main():
    " Menu-loop. Exit with KeyboardInterrupt."
    db_tool = get_db_tool()
    query = ["Not set.", []]
    threshold = 1.0
    menu = {
        "1": ["1: Searches DB selectively.", db_tool.query_threshold_selective],
        "2": ["2: Searches DB entirely.", db_tool.query_threshold_all]
    }
    try:
        while True:
            # // Display.
            print()
            for item in menu: print(menu.get(item)[0])
            # // Action.
            select = input(":")
            if select in menu: 
                set_query(previous=query, db_tool=db_tool)
                data = menu.get(select)[1](q_siminet=query[1],threshold=threshold)
                display_data(data)
    except KeyboardInterrupt:
        pass

main()