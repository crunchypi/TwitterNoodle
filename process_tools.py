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
    # //    Format: [recursion_lvl, query, word, confidence]
    def get_similarity_net(self, query:list, current_recursion:int = 0, max_recursion:int = 2):
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
        return calculate(query, current_recursion, max_recursion)


    def get_score(self, new:str, existing:str, degrees:int = 2): # // Arbitrary scoring system...
        # // Note: add degree filter range?
        total_score = 0
        
        result_new = self.get_similarity_net(new.split(), max_recursion = degrees)
        result_existing = self.get_similarity_net(existing.split(), max_recursion = degrees)
        
        for item_new in result_new:
            for item_existing in result_existing:
                word_a = item_new[2]
                word_b = item_existing[2]
                
                if word_a in word_b or word_b in word_a or word_a == word_b:
                    # // + 1 because degrees start at 0. Might wanna change that..
                    total_score += item_existing[3] / (item_existing[0] + 1)
                    
        return total_score

    def get_score_from_uncompressed_siminet(self, new: list, existing: list) -> float:
        """ Gets score from two similarity nets
        """
        total_score = 0
        for item_new in new:
            for item_existing in existing:
                if word_a in word_b or word_b in word_a or word_a == word_b:
                    total_score += item_existing[3] / (item_existing[0] + 1)
        return total_score

    def get_top_simi_index(self, new_object:DataObj, old_objects:list, degrees:int = 2):
        # // Finds the best similarity match between an object and a list of objects.
        score_highest = 0 
        index = 0 ## What if nothing matches? @@@
        for i, obj in enumerate(old_objects):
            score_current:int = self.get_score(new=new_object.text, existing=obj.text, degrees=degrees)
            self.cond_print(f"{new_object.text} + {obj.text} = {score_current}")
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