import gensim.downloader as api
from packages.cleaning.data_object import DataObj

# // Model Info:
# //    https://raw.githubusercontent.com/RaRe-Technologies/gensim-data/master/list.json
# //    https://radimrehurek.com/gensim/downloader.html

class ProcessSimilarity():
        
    w2v_model = None
    verbosity = False

    def __init__(self, verbosity: bool = False):
        self.verbosity = verbosity

    def get_model_info(self, name="glove-twitter-25"): # // for pre-made
        api.info(name)

    def cond_print(self, msg):
        if self.verbosity: print(msg)

    def load_model(self, name="glove-twitter-25"): # // pre-made
        self.cond_print("Loading model...")
        self.w2v_model = api.load("glove-twitter-25")
        self.cond_print("Done loading model.")

    # // This creates a list of simularity net results. 
    # //    Format uncompressed: [recursion_lvl, query, word, confidence]
    # //    Format compressed: [word, confidence]
    def get_similarity_net(self, 
                           query:list, 
                           current_recursion:int = 0, 
                           max_recursion:int = 2,
                           compress = True):
        if self.w2v_model is None:
            self.cond_print("Word 2 Vector model not set, aborting.")
            return
        self.cond_print(f"Starting similarity fetch for: {query}.")

        def calculate(query:list, current_recursion:int, max_recursion:int):
            # // Format: [[recursion_lvl, query, match, confidence_score]]
            # // Note: Consider using generator, might be a good idea for high max_recursion..
            if current_recursion >= max_recursion: return False
            current_degree = []
            for word in query:
                try:
                    sim_lst = self.w2v_model.most_similar(word)
                    for item in sim_lst:
                        next_query = [item[0]]
                        current_degree.append([current_recursion, word, item[0],item[1]] )
                        
                        result = calculate(next_query, current_recursion + 1, max_recursion)
                        if result: current_degree.extend(result)
                except KeyError:
                    pass
            return current_degree

        self.cond_print(f"Ended similarity fetch for: {query}.")
        result = calculate(query, current_recursion, max_recursion)
        if compress: result = self.compress_similarity_net(result)
        return result

    def compress_similarity_net(self, lst):
        lst = lst.copy()
        new_lst = []
        for i in range(len(lst)):
            current_item = lst.pop()
            current_word = current_item[2]
            previous_words = [ item[0] for item in new_lst]
            
            if current_word in previous_words: continue 
            
            current_score = current_item[3] / (current_item[0] + 1)
            for other_item in lst:
                other_word = other_item[2]
                if current_word == other_word:
                    # // + 1 because degrees start at 0. Might wanna change that.. @@
                    current_score += other_item[3] / (other_item[0] + 1)
            new_lst.append([current_word, current_score])
        return new_lst



    def get_score_from_str(self, new:str, existing:str, degrees:int = 2):
        # // Note: add degree filter range? @@
        result_new = self.get_similarity_net(new.split(), max_recursion = degrees)
        result_existing = self.get_similarity_net(existing.split(), max_recursion = degrees)
        return self.get_score_compressed_siminet(new=result_new, other=result_existing)

    def get_score_compressed_siminet(self, new:list, other:list):
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
                           mode:str = "siminet_compressed"):
        # // Finds the best similarity match between an object and a list of objects,
        # // based on two modes:
        # //    text = will access DataObj.text
        # //    siminet = will acced DataObj.siminet_compressed (precomputed siminet)
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
                score_current = self.get_score_from_str(new=new_object.text, 
                                                        existing=other.text, 
                                                        degrees=degrees)
            else:
                score_current = self.get_score_compressed_siminet(new=new_object.siminet_compressed,
                                                                  other=other.siminet_compressed)
            self.cond_print(f"{new_object.text} + {other.text} = {score_current}")
            if score_current > score_highest:
                score_highest = score_current
                index = i
        return index


def test():
    ps = ProcessSimilarity(True)
    ps.load_model()
    query = "window"
    txt = [
        "car",
        "bus",
        "cat",
        "dog",
        "economy",
        "money"
    ]
    for item in txt:
        score = ps.get_score(query, item , 2)
        print(f"{query} + {item} = {score}")
#test()