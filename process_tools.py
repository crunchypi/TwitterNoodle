import gensim.downloader as api
from packages.cleaning.data_object import DataObj

# // Model Info:
# //    https://raw.githubusercontent.com/RaRe-Technologies/gensim-data/master/list.json
# //    https://radimrehurek.com/gensim/downloader.html

class ProcessSimilarity():
        
    w2v_model = None
    verbosity = False

    def __init__(self, verbosity:bool = False) -> None:
        "Initialisation with verbosity specification."
        self.verbosity = verbosity

    def get_model_info(self, name:str="glove-twitter-25") -> None: # // for pre-made
        "Get some info about a model."
        api.info(name)

    def cond_print(self, msg:str) -> None:
        "'Custom' print which prints only if verbosity is enabled."
        if self.verbosity: print(msg)

    def load_model(self, name:str ="glove-twitter-25") -> None: # // pre-made
        "Load a model into this class for further use (siminet creation)."
        self.cond_print("Loading model...")
        self.w2v_model = api.load("glove-twitter-25")
        self.cond_print("Done loading model.")

    # // This creates a list of simularity net results. 
    # //    Format uncompressed: [recursion_lvl, query, word, confidence]
    # //    Format compressed: [word, confidence]
    def get_similarity_net(self, 
                           query:list, 
                           current_recursion:int = 0, # // Remove? @
                           max_recursion:int = 2,
                           compress:bool = True) -> list:
        """ Wrapper for similarity net creator, containing the creator, with some 
            necessary safety checks and additional operations, mainly siminet compression.

            The siminet creator itself (called 'calculate') goes through each query
            word in a list and gets similar words, which are passed into the function
            again recursively. For each branch, the query is added to a collection, 
            along with where it came from (what word was used to get it through the model),
            recursion level, and confidence level. The format is:
                [[recursion_lvl, query, match, confidence_score]]
            The recursion/branching is limited by the 'max_recursion' param.

            'compress' param passes the siminet to 'compress_similarity_net' method
            before this method does a return, such that the siminet is compressed. 
            This removes duplicates while preserving the correct score. 
            Recursion_lvl and query(camefrom) is removed as well.
        """
        if self.w2v_model is None:
            self.cond_print("Word 2 Vector model not set, aborting.")
            return
        self.cond_print(f"Starting similarity fetch for: {query}.")

        def calculate(query:list, current_recursion:int, max_recursion:int) -> list:
            # // TODO: Back-references?
            if current_recursion >= max_recursion: return False # // Exit clause.
            current_degree = []
            for word in query:
                try:
                    sim_lst = self.w2v_model.most_similar(word) # // Query w2v
                    for item in sim_lst:
                        next_query = [item[0]] # // next query, chunked. 
                        current_degree.append([current_recursion, word, item[0],item[1]]) # // Save.
                        
                        result = calculate(next_query, current_recursion + 1, max_recursion) # // Recurs.
                        if result: current_degree.extend(result) # // Save.
                except KeyError:
                    pass
            return current_degree # // Give back.

        result = calculate(query, current_recursion, max_recursion)
        # // Add the original keywords to result:
        #for item in query: result.insert(0, [0, item, item, 1]) # // Note: Removed while backref isn't fixed.
        self.cond_print(f"Ended similarity fetch for: {query}.") 
        if compress: result = self.compress_similarity_net(result)
        return result


    def compress_similarity_net(self, lst:list) -> list:
        """ Takes this format of a standard siminet:
                [[recursion_lvl, query, match, confidence_score]]
            and creates a new one without any duplicates, recursion levels, 
            or 'came-from' values, which are noted as 'query' in the example above.
            Returns the compressed siminet in this form:
                [[word, confidence_score]]
        """
        lst = lst.copy()
        new_lst = []
        for i in range(len(lst)):
            current_item = lst.pop()
            current_word = current_item[2]
            previous_words = [item[0] for item in new_lst]
            
            if current_word in previous_words: continue # // No recalc/duplicates
            
            current_score = current_item[3] / (current_item[0] + 1)
            for other_item in lst:
                other_word = other_item[2]
                if current_word == other_word:
                    # // + 1 because degrees start at 0. Might wanna change that.. @@
                    current_score += other_item[3] / (other_item[0] + 1)
            new_lst.append([current_word, current_score])
        return new_lst


    def get_score_from_str(self, new:str, existing:str, degrees:int = 2) -> float:
        # // Note: add degree filter range? @@
        """ Takes two texts/sentences/words (str) and fetches a siminet for both,
            before passing it along to a scoring system, and returning the result.
        """
        result_new = self.get_similarity_net(new.split(), max_recursion = degrees)
        result_existing = self.get_similarity_net(existing.split(), max_recursion = degrees)
        return self.get_score_compressed_siminet(new=result_new, other=result_existing)

    def get_score_compressed_siminet(self, new:list, other:list):
        """ Takes two siminets and compares words. Upon match, the total
            score is increased by the siminet score values for those words.
            Returns total score.
        """
        total_score = 0
        for item_new in new:
            for item_other in other:
                word_a = item_new[0]
                word_b = item_other[0]
                # // Could replace with +- 1 letter similarity margin?
                if word_a == word_b:
                    # // Rudimentary scoring system.
                    total_score += (item_new[1] + item_other[1])
                    
        return total_score


    def get_top_simi_index(self, 
                           new_object:DataObj, 
                           other_objects:list, 
                           degrees:int = 2,
                           mode:str = "siminet_compressed") -> int:
        """ Takes a DataObj (lets call it 'A') and a list of other DataObj (lets call them 'B').
            'A' is matched against all items in 'B' to find which one if B is most similar to 'A'.
            This can be done in two ways:
                1: Create a new siminet for all DataObj and do a score. This is done
                    with the mode (param) 'text'. This uses the degrees param.
                2: Use the siminet of all DataObj (without creating new ones) and skip
                    directly to scoring. Done with the mode (param) 'siminet_compressed'
                    This naturally requires that all DataObj already have siminets (compressed) 
                    cached, otherwise the result will always crash. This option is naturally 
                    a lot faster than option 1 though.
            
        """
 
        valid_modes = ["text", "siminet_compressed"]
        if mode not in valid_modes: 
            self.cond_print("ProcessSimilarity.get_top_simi_index(): "+
                             f"selected mode '{mode}' is invalid. Aborting.")
            return

        score_highest = 0 
        index = None
        for i, other in enumerate(other_objects):
            score_current = 0
            if mode == "text":
                # // new_obj data could probably be stored before loop... @@
                score_current = self.get_score_from_str( # 
                    new=new_object.text, 
                    existing=other.text, 
                    degrees=degrees)
            else:
                score_current = self.get_score_compressed_siminet(
                    new=new_object.siminet_compressed,
                    other=other.siminet_compressed)

            self.cond_print(f"{new_object.text} + {other.text} = {score_current}")
            if score_current > score_highest:
                score_highest = score_current
                index = i
        return index

