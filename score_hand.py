import operator
import itertools
from collections import defaultdict
from functools import partial

LETTER_MAP = {"a": 1, "c": 3, "b": 3, "e": 1, "d": 2, "g": 2, 
               "f": 4, "i": 1, "h": 4, "k": 5, "j": 8, "m": 3, 
               "l": 1, "o": 1, "n": 1, "q": 10, "p": 3, "s": 1, 
               "r": 1, "u": 1, "t": 1, "w": 4, "v": 4, "y": 4, 
               "x": 8, "z": 10}

def raw_word_score(word):
    return sum(map(LETTER_MAP.get, word))

def make_dict(dict_file='scrabble.dict'):
    with open(dict_file, 'r') as fp:
        return defaultdict(int, {word: raw_word_score(word) 
                                 for word in map(lambda w: 
                                                 w.strip().lower(), fp)})

def raw_hand_perms(hand):
    return set(''.join(p) for i in range(len(hand)) 
               for p in itertools.permutations(hand, i))

def raw_hand_scores(hand, word_dict, top_k=10):
    all_words = {word: word_dict[word] for word in raw_hand_perms(hand)}
    sorted_scores = sorted(all_words.items(), key=operator.itemgetter(1))
    return sorted_scores[-top_k:]

class ScrabbleHelper(object):
    def __init__(self, scrabble_dict='scrabble.dict'):
        self._raw_dict = make_dict(scrabble_dict)

    def print_raw_hand_scores(self, hand, top_k=5):
        for word, score in reversed(
                raw_hand_scores(hand, self._raw_dict, top_k)):
            print('{}: {}'.format(word, score))
