import gensim.downloader as api
from packages.cleaning.data_object import DataObj
from packages.cleaning.basic_cleaner import BasicCleaner

# // Model Info:
# //    https://raw.githubusercontent.com/RaRe-Technologies/gensim-data/master/list.json
# //    https://radimrehurek.com/gensim/downloader.html

class ProcessSimilarity():
        
    """ This class is responsible for handling similarities.
        This is done with a few main features;
            - Creating a 'similarity net'(tree) and compressing it.
                This is done with a word2vec model.
            - Compare two similarity nets to get a similarity 
                score.
            - Compare a dataobject agains a list of other dataobjects
                to find one in the list which is most similar.
            - Sort a list of dataobjects by similarity 
                (get representatives)
        NOTE; a 'self.w2v_model' must be set for most of these
            methods to work. This can either be done internally
            by calling 'self.get_model()' or by setting it 
            externally (if the model is shared).
        NOTE: Throughout this class, the names 'dataobjects',
            'dataobj', or something along those lines will be used.
            This refers to packages.cleaning.data_object.
    """

    def __init__(self, verbosity:bool = False) -> None:
        "Initialisation with verbosity specification."
        self.verbosity = verbosity

        self.w2v_model = None
        self.verbosity = False

    def get_model_info(self, name:str="glove-twitter-25") -> None: # // for pre-made
        "Print some info about a model."
        api.info(name)

    def cond_print(self, msg:str) -> None:
        "'Custom' print which prints only if self.verbosity is True."
        if self.verbosity: print(msg)

    def load_model(self, name:str ="glove-twitter-25") -> None: # // pre-made
        "Load a w2v model into this instance for further use (siminet creation)."
        self.cond_print("Loading model...")
        self.w2v_model = api.load("glove-twitter-25")
        self.cond_print("Done loading model.")


    def get_similarity_net(self, 
                           query:list, 
                           max_recursion:int = 2) -> list:
        """ Wrapper for similarity net creator, containing the creator and some  
            necessary safety checks and additional operations, mainly siminet compression.

            The siminet creator itself (called 'calculate') goes through each query
            word in a list and gets similar words, which are passed into the function
            again recursively. For each branch, the query is added to a collection, 
            along with where it came from (what word was used to get it through the model),
            recursion level, and confidence level. The format is:
                [[recursion_lvl, query, match, confidence_score], ... ]
            The recursion/branching is limited by the 'max_recursion' param.
            NOTE max_recursion < 1 is prohibited and will raise a ValueError.

            This similarity net created by 'calculate' will get automatically
            compressed to remove back- and cross-referencing (words appearing
            more than once in the siminet). This will create a new format:
                [[word, confidence_score], ...]
            This is forced but can be manually disabled at the return line.
        """
        # // Do setup check and value check.
        if self.w2v_model is None:
            self.cond_print("Word 2 Vector model not set, aborting.")
            return
        if max_recursion < 1: raise ValueError("Expected minimum recursion of 1")
        self.cond_print(f"Starting similarity fetch for: {query}.")
        
        def validate_next(content:str) -> bool:
            " Validate a word before more recursion (performance boost)."
            # // Signal bracn abort if there is a non-alpha.
            for char in content: 
                if not char.isalpha(): 
                    return False
            # // Signal branch abort if len is insufficient (arbitrary len)
            if len(content) < 2: return False 
            return True

        def calculate(query:list, current_recursion:int, max_recursion:int) -> list:
            "Create similarity net, see wrapper docstring for more information"
            if current_recursion >= max_recursion: return [] # // Exit clause.
            current_degree = []
            for word in query:
                try: # // Try because some wors may not be in the w2v model.
                    sim_lst = self.w2v_model.most_similar(word) # // Query w2v.
                    for item in sim_lst:
                        next_query = [item[0]] # // next query, chunked. 
                         # // Drop non-alpha and with insufficient len
                        if validate_next(item[0]):
                            # // Save to collection.
                            current_degree.append(
                                [current_recursion, word, item[0],item[1]]
                            )
                            # // Create new branch(recursion)
                            result = calculate(
                                next_query, 
                                current_recursion + 1, 
                                max_recursion
                            )
                            # // Save if any.
                            if result: current_degree.extend(result)
                except KeyError:
                    pass 
            return current_degree # // Give back branch.

        # // Get siminet, compress it and return.
        result = calculate(query, 0, max_recursion)
        self.cond_print(f"Ended similarity fetch for: {query}.") 
        return self.compress_similarity_net(result)


    def compress_similarity_net(self, lst:list) -> list:
        """ Takes this format of a standard siminet(created by 
            calculate() in self.get_similarity_net()):
                [[recursion_lvl, query, match, confidence_score], ...]
            and creates a new one without any duplicates, recursion levels, 
            or 'came-from' values, which are noted as 'query' in the example above.
            Returns the compressed siminet in this form:
                [[word, confidence_score], ...]
        """
        lst = lst.copy()    # // Redundancy.
        new_lst = []        # // Collection for end result.
        for i in range(len(lst)):
            current_item = lst.pop()
            current_word = current_item[2] # // Accessing new word.

            # Skip duplicates and re-calculations.
            previous_words = [item[0] for item in new_lst]
            if current_word in previous_words: continue
            
            # // Divide simi score by recursion depth. + 1 because ..
            # // .. recursion depth starts at 0.
            calc_score = lambda score, depth: score / (depth + 1)
            
            # // Score of current word.
            current_score = calc_score(
                score = current_item[3],
                depth = current_item[0]
            )
            # // Check current against all others in siminet to ..
            # // .. cumulate score on duplicates. Only one occurence ..
            # // .. of a word will remain.
            for other_item in lst:
                other_word = other_item[2]
                if current_word == other_word:
                    # // Add to current score if word appears more  ..
                    # // .. than once in the original list.
                    current_score += calc_score(
                        score= other_item[3],
                        depth=other_item[0]
                    )
            # // Save.
            new_lst.append([current_word, current_score])
        return new_lst


    def get_score_compressed_siminet(self, new:list, other:list) -> float:
        " Takes two compressed siminets and compares them to get a score. "
        total_score = 0
        for item_new in new:
            for item_other in other:
                # // Unpacking for clarity.
                word_a = item_new[0]
                score_a = item_new[1]
                word_b = item_other[0]
                score_b = item_other[1]
                # // Identical words will increment total_score symmetrically.
                if word_a == word_b: total_score += (score_a + score_b)
                    
        return total_score


    def get_top_simi_index(self, 
                           new_object:DataObj, 
                           other_objects:list) -> int: # // OR None.
        """ Takes a DataObj and matches its siminet agains the siminet of other
            DataObj in a list. The return will be an index(int) to the list,
            pointing to the best match.
            NOTE: Can return None if there is no match at all.
            Exceptions: ValueError if any of the dataobjects lack a siminet
        """
        # // Check if siminet exists.
        error_suffix = "does not have a simi-net."
        if new_object.siminet == None: raise ValueError(f"'new_object' {error_suffix}")
        for other in other_objects: 
            if other.siminet == None: 
                raise ValueError(f"'other' {error_suffix}")

        # // Get top index.
        score_highest = 0 
        index = None
        for i, other in enumerate(other_objects):
            # // Get similarity score
            score_current = self.get_score_compressed_siminet(
                    new=new_object.siminet,
                    other=other.siminet
            )
            self.cond_print(f"'{new_object.text}' + '{other.text}' = {score_current}")
            # // Update highest if necessary.
            if score_current > score_highest:
                score_highest = score_current
                index = i
        return index


    def get_representatives(self, objects:list) -> list:
        """ Takes in a list of DataObjects, sorts it by similarity and returns 
            a list: [status:bool, [sorted_objects]], where status refers to
            whether or not the sorted list order is new (as in, not identical
            to the parameter list order).

            Sorting by similarity means that the closer
            an object is to index 0, the more similar it is to all objects.
            DataObj on index zero should represent all other DataObjects.

            Note: This naturally means that an object list has to contain
            more than two objects, because representative of two doesn't make
            sense in this context. In these cases, the status bool in the returned
            list will always be False.

            Exception: ValueError if any object lacks a siminet.
        """ 

        # // Reject lack of siminet
        for x in objects: 
            if x.siminet == None: raise ValueError(
            "Object does not have a simi-net."
        )


        def sorting_helper(score_dict: dict):
            "Return key with highest integer value in a dict."
            highscore = 0
            highscore_key = None
            keys = list(score_dict.keys())
            for key in keys:
                key_value = score_dict.get(key)
                if key_value > highscore:
                    highscore = key_value
                    highscore_key = key
            return highscore_key

        objects = objects.copy()
        sorted_objects = []
        if len(objects) > 2: # // Sort only if there are enough DataObjects.
            # // Get incedes of representatives in objects:[DataObj]. 
            # // Each mention of N adds N to mentions_by_index.
            mentions_by_index = []
            for obj in objects:
                other_list = [other for other in objects # // Make a list without current obj.
                                 if other.unique_id != obj.unique_id]
                target = self.get_top_simi_index(new_object=obj, other_objects=other_list)
                mentions_by_index.append(target)
            # // Create dict structure where {obj_index : total_mentions}
            score_dict = {index : 0 for index in range(len(objects))}
            # // Distribute mentions from (mentions_by_index) into
            # // the dictionary, which keys represent objects(by index).
            for dict_index in range(len(objects)):
                for mentions_index in mentions_by_index:
                    if mentions_index == dict_index:
                        score_dict[dict_index] += 1
            # // Unpack dict data into sorted_objects for end result.
            for _ in range(len(objects)):
                top_index = sorting_helper(score_dict)
                if top_index != None:
                    sorted_objects.append(objects[top_index])
                    del score_dict[top_index] # // Clear key with top score.
                else: 
                    # // No highscore is found, meaning that remaining scores
                    # // are all 0. Now remaining indeces can be added at the 
                    # // end of the sorted list.
                    remaining_indeces = list(score_dict.keys())
                    for i in remaining_indeces:
                        sorted_objects.append(objects[i])
                    break

        else: # // Not possible to sort in a meaningful way, return as is.
            return [False, objects]

        for index in range(len(objects)): # // check if order has changed.
            if objects[index].unique_id != sorted_objects[index].unique_id:
                return [True, sorted_objects]
        #// If this return is hit, then order is not new.
        return [False, sorted_objects]