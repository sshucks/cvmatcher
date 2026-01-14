from typing import List, Set, Dict, Any, Type
from collections import Counter
from itertools import groupby, tee
from operator import itemgetter

class MajorityVotingFieldStrategy():
    """
    Abstract class for defining a majority voting strategy of LLM JSON responses
    """

    def __init__(self, key:str):
        """
        Initialize the strategy by specifying a JSON key to apply the strategy on
        :param key: JSON key
        """
        self.key = key
    
    def apply(self, data: List,  m:int, n:int) -> Any:
        """
        Apply the strategy on the data
        :param data: list of JSON data
        :param m: minimum number of responses that share the content
        :param n: total number of responses
        :return: Any
        """
        raise NotImplementedError
    
class ListObjectMajorityVotingStrategy(MajorityVotingFieldStrategy):

    def __init__(self, key:str, id_parts: List, list_aggreagte:List = []):
        """
        Initialize majority voting strategy to handle objects in a JSON list
        :param key: JSON key to apply the strategy on
        :param id_parts: list of keys to combine to an ID that is used to check the majority
        :param list_aggreagte: list of field names that represent JSON lists that need to be majority voted on
        """
        MajorityVotingFieldStrategy.__init__(self, key)
        self.id_parts = id_parts
        if list_aggreagte:
            self.list_aggregation_strats = {field : ListIntersectionMajorityVotingStrategy(field) for field in list_aggreagte}
        else:
            self.list_aggregation_strats = None
    
    
    def get_id(self, entry):
        """
        Generate ID of a JSON object based on the specified ID parts
        :param entry: JSON entry
        :return: generated ID
        """
        id = ""
        for part in self.id_parts:
            if part in entry:
                id = id + "_" + str(entry[part])
        return id
    
    def apply(self, data: List[Dict], m:int, n:int) -> Dict:
        """
        Perform majority voting by using all list elements of all responses
        :param data: list of JSON data
        :param m: minimum number of responses that share the content
        :param n: total number of responses
        :return: Dict of aggregated partial data
        """

        # filtered data for the key of interest
        filtered_data = [x[self.key] for x in data]

        # compile a list of lists which hold all occuring values
        value_sets = []
        for data in filtered_data:
            ids = set()
            for entry in data:
                id = self.get_id(entry)
                entry['id'] = id
                ids.add(id)
            value_sets.append(list(ids))
            
        value_sets = sum(value_sets, []) # flatten list of lists

        # count which objects have a minimum count of m and select them
        counts = Counter(value_sets)
        values_to_select = {item for item, count in counts.items() if count >= m}
        selected_data = [x for x in filtered_data for y in x if y['id'] in values_to_select]

        selected_data = sum(selected_data, [])
        sorted_data = sorted(selected_data, key=itemgetter('id'))
        result:List = []

        # iterate grouped data
        for key, group_iterator in groupby(sorted_data, key=itemgetter('id')):
            group_one, group_two = tee(group_iterator) # create two iterators to process without losing entries
            first_entry = next(group_iterator) # select first entry, since important attributes (defined by id parts) are equal

            # aggregate nested element using another, define majority voting strategy
            if self.list_aggregation_strats != None:
                for listField, strategy in self.list_aggregation_strats.items():
                    majorityList = strategy.apply(list(group_two), m,n ) #  apply strategy
                    first_entry[listField] = majorityList # replace entry in object with aggregated result
            result.append(first_entry)

        # remove id property from entries
        for r in result:
            r.pop('id', None)
        return result

class ObjectMajoritVotingStrategy(MajorityVotingFieldStrategy):

    def __init__(self, key:str):
        """
        Initialize majority voting strategy to handle JSON objects
        :param key: JSON key to apply the strategy on
        """
        MajorityVotingFieldStrategy.__init__(self, key)

    def apply(self, data: List[Dict], m:int, n:int) -> Dict:
        """
        Perform majority voting by using all properties of a JSON object
        :param data: list of JSON data
        :param m: minimum number of responses that share the content
        :param n: total number of responses
        :return: Dict of aggregated partial data
        """
        # filter data for given key
        filtered_data = [x[self.key] for x in data]

        # init dict with empty lists
        values = {}
        for key in filtered_data[0].keys():
            values[key] = []

        # append values to the lists
        for d in filtered_data:
            for k in d.keys():
                values[k].append(d[k])

        # for each dict entry, compile the counts of values, filter for a minimum of m occurrences and select the first value
        results = {}
        for key in values.keys():
            counts = Counter(values[key])
            value_to_select = {item for item, count in counts.items() if count >= m}
            if len(value_to_select) == 1:
                results[key] = list(value_to_select)[0]
            else:
                raise ValueError(f"multiple values to select for data[{self.key}][{key}]")

        return results

class SingleValueListMajorityVotingStrategy(MajorityVotingFieldStrategy):
    def __init__(self, key:str):
        """
        Initialize majority voting strategy to handle fields that hold a single value
        :param key: JSON key to apply the strategy on
        """
        MajorityVotingFieldStrategy.__init__(self, key)
    
    def apply(self, data: List[Dict], m:int, n:int) -> Any:
        """
        Perform majority voting by finding the most common value of a field
        :param data: list of JSON data
        :param m: minimum number of responses that share the content
        :param n: total number of responses
        :return: Most abundant value for the given field, with respect to m and n
        """

        # filter the input data for the given key
        filtered_data = [x[self.key] for x in data]
       
        # flatten list of lists
        values = sum(filtered_data, [])

        # count object occurrences and filter for a minimum of m occurrences
        counts = Counter(values)

        counts = sorted(counts.items(), reverse=True) # sort descending
        counts = dict(counts)
        value_to_select = {item for item, count in counts.items() if count >= m}

        # take the most frequent value that is above m
        if len(value_to_select) == 1:
            return list(value_to_select)[0] 
        else:
            raise ValueError
    
class SingleValueMajorityVotingStrategy(MajorityVotingFieldStrategy):
    def __init__(self, key:str):
        """
        Initialize majority voting strategy to handle fields that hold a single value
        :param key: JSON key to apply the strategy on
        """
        MajorityVotingFieldStrategy.__init__(self, key)
    
    def apply(self, data: List[Dict], m:int, n:int) -> Any:
        """
        Perform majority voting by finding the most common value of a field
        :param data: list of JSON data
        :param m: minimum number of responses that share the content
        :param n: total number of responses
        :return: Most abundant value for the given field, with respect to m and n
        """

        # filter the input data for the given key
        filtered_data = [x[self.key] for x in data]
       
        # flatten list of lists
        values = filtered_data

        # count object occurrences and filter for a minimum of m occurrences
        counts = Counter(values)

        counts = sorted(counts.items(), reverse=True) # sort descending
        counts = dict(counts)
        value_to_select = {item for item, count in counts.items() if count >= m}

        # take the most frequent value that is above m
        if len(value_to_select) == 1:
            return list(value_to_select)[0] 
        else:
            raise ValueError

class ListIntersectionMajorityVotingStrategy(MajorityVotingFieldStrategy):
    def __init__(self, key:str):
        """
        Initialize majority voting strategy to handle simple entries of list
        :param key: JSON key to apply the strategy on
        """
        MajorityVotingFieldStrategy.__init__(self, key)

    def apply(self, data: List, m:int, n:int)->List:
        """
        Perform majority voting by using all list entries of all responses
        :param data: list of JSON data
        :param m: minimum number of responses that share the content
        :param n: total number of responses
        :return: List of aggregated data
        """
        value_sets = []

        for d in data:
            value_sets.append(d[self.key])

        value_sets = sum(value_sets, [])  # flatten list of lists
        counts = Counter(value_sets)
        values_to_select = {item for item, count in counts.items() if count >= m}

        return list(values_to_select)

class MajorityVoting():

    def __init__(self, m:int = 2, n:int = 3):
        """
        Majority Voting Implementation for LLM JSON Responses
        :param m: minimum number of responses that share the content
        :param n: total number of responses
        """
        self.m = m
        self.n=n
        self.voting_strategy:dict[str, MajorityVotingFieldStrategy] = {}

    def set_n(self, n:int):
        """
        Setter of the total number of responses
        :param n: total number of responses
        :return: void
        """
        self.n = n
    
    def set_m(self, m:int):
        """
        Setter of minimum number of responses that share the content
        :param m: minimum number of responses that share the content
        :return: void
        """
        self.m = m
    
    def set_strategies(self, mapping: Dict[str, MajorityVotingFieldStrategy]):
        """
        Set the strategies to apply on the data.
        :param mapping: Dictionary specifying a key in the JSON response and the according strategy to apply
        :return: None
        """
        self.voting_strategy = mapping

    def apply_voting(self, data: List) -> Dict:
        """
        Apply the specified majority voting strategie for each key
        :param data: list of JSON data to perform majority voting on
        :return: Dict of the majority aggregated JSON data
        """
        

        majority_voted = {}
        for key, value in self.voting_strategy.items():
            majority_voted[key] = value.apply(data, m = self.m, n=self.n)

        return majority_voted


