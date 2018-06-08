import os
import sys
import unittest
import operator
import random
import itertools
from collections import defaultdict, namedtuple
from functools import partial

from board import ScrabbleBoard, SpotType

LETTER_MAP = {"a": 1, "c": 3, "b": 3, "e": 1, "d": 2, "g": 2,
               "f": 4, "i": 1, "h": 4, "k": 5, "j": 8, "m": 3,
               "l": 1, "o": 1, "n": 1, "q": 10, "p": 3, "s": 1,
               "r": 1, "u": 1, "t": 1, "w": 4, "v": 4, "y": 4,
               "x": 8, "z": 10}
DICT_FILE = (lambda dname:
             (lambda pd: os.path.join(pd[0], dname))(
                 next(filter(lambda rdf:
                             dname in rdf[2], os.walk('.')))))('scrabble.dict')

def raw_word_score(word):
    return sum(map(LETTER_MAP.get, word))

def make_dict(dict_file=DICT_FILE):
    with open(dict_file, 'r') as fp:
        return defaultdict(int, {word: raw_word_score(word)
                                 for word in map(lambda w:
                                                 w.strip().lower(), fp)})

def raw_hand_perms(hand):
    return set(''.join(p) for i in range(1, len(hand) + 1)
               for p in itertools.permutations(hand, i))

def raw_hand_scores(hand, word_dict, top_k=10):
    all_words = {word: word_dict[word] for word in raw_hand_perms(hand)}
    sorted_scores = sorted(all_words.items(), key=operator.itemgetter(1))
    return sorted_scores[-top_k:]

class NotAWordException(Exception):
    pass

class ScrabbleHelper(object):
    Play = namedtuple('Play', ('location', 'vertical', 'letters'))

    def __init__(self, scrabble_dict=DICT_FILE, board=None):
        self._raw_dict = make_dict(scrabble_dict)
        self._board = board or ScrabbleBoard()

    def print_raw_hand_scores(self, hand, top_k=5):
        for word, score in reversed(
                raw_hand_scores(hand, self._raw_dict, top_k)):
            print('{}: {}'.format(word, score))

    def _get_start(self, loc, vertical):
        next_ = lambda l: (l[0], l[1] - 1) if vertical else (l[0] + 1, l[1])
        prev = lambda l: (l[0], l[1] + 1) if vertical else (l[0] - 1, l[1])
        in_bounds = lambda l: all(comp >= 0 for comp in l)
        prefix = lambda l: (in_bounds(prev(l))
                            and self._board[prev(l)][1] is not None)
        while prefix(loc):
            loc = prev(loc)
        return loc, next_

    def _score_major(self, play):
        mult = 1
        score = 0
        word = ''
        touched = False

        letter_locs = []
        start, next_loc = self._get_start(play.location, play.vertical)
        for letter in play.letters:
            while self._board[start][1] is not None:
                touched = True
                score += 0 if self._board[start][1].is_blank else \
                    LETTER_MAP[self._board[start][1].letter]
                word += self._board[start][1].letter
                start = next_loc(start)

            letter_score = LETTER_MAP[letter]

            pt = self._board[start][0]
            if pt == SpotType.double_word:
                mult *= 2
            elif pt == SpotType.triple_word:
                mult *= 3
            elif pt == SpotType.double_letter:
                letter_score *= 2
            elif pt == SpotType.triple_letter:
                letter_score *= 3

            letter_locs.append(start)
            score += letter_score
            word += letter
            start = next_loc(start)

        # Could be some extra pieces to make word longer
        while self._board[start][1] is not None:
            touched = True
            score += 0 if self._board[start][1].is_blank else \
                LETTER_MAP[self._board[start][1].letter]
            word += self._board[start][1].letter
            start = next_loc(start)

        if len(word) == 1:
            return 0, None, touched
        if word not in self._raw_dict:
            raise NotAWordException(word)
        return score * mult, letter_locs, touched

    # TODO: Not handling blank pieces in hand.
    def _score_play(self, play):
        try:
            is_attached = False
            # This should return what the blank/s was/were possibly can be, then
            # pass these values to each successive call to _score_minor to refine
            # them. Either each has at least one possible value by the end, or
            # abort
            major_score, letter_locs, touched = self._score_major(play)
            is_attached = is_attached or touched
            # This will be None if the score-able word is only 1 character
            # long
            if letter_locs is None:
                return 0

            minor_scores = []
            for loc, letter in zip(letter_locs, play.letters):
                aux_play = self.Play(loc, not play.vertical, letter)
                minor_score, _, touched = self._score_major(aux_play)
                minor_scores.append(minor_score)
                is_attached = is_attached or touched

            if not is_attached:
                return 0

            return (major_score + sum(minor_scores) +
                    (50 if len(play.letters) == 7 else 0))
        except (KeyError, NotAWordException) as nwe:
            return 0

    def _all_plays(self, hand):
        permed_hand = raw_hand_perms(hand)

        play_scores = {}
        #for location in ((13, 10),): # self._board.open_tiles:
        for location in self._board.open_tiles:
            for letters in permed_hand:
                for vertical in (True, False):
                    play = self.Play(location, vertical, letters)
                    play_scores[play] = self._score_play(play)

        return sorted(play_scores.items(), key=operator.itemgetter(1))

    def best_plays(self, hand, top_k=5):
        sorted_plays = self._all_plays(hand)
        for p, _ in zip(reversed(sorted_plays), range(top_k)):
            print('{} with score of {}'.format(*p))
        return sorted_plays[-1][0]

class TestScrabbleHelper(unittest.TestCase):
    sh = ScrabbleHelper(
        board=ScrabbleBoard().place_word('waggoning', (5, 7))
        .place_word('snowcats', (5, 10), vertical=True)
        .place_word('whizzing', (8, 14), vertical=True, blanks=(3, 4))
        .place_word('gliders', (7, 7), vertical=True, blanks=(3,))
        .place_word('dad', (10, 9), vertical=False)
        .place_word('to', (13, 4), vertical=False)
        .place_word('pass', (10, 5), vertical=False)
    )

    def test_lare(self):
        choices = self.sh._all_plays('lare')
        self.assertEqual(choices[-1][1], 18)
        self.assertEqual(choices[-2][0].letters, 'ale')

    def test_uqikoj(self):
        choices = self.sh._all_plays('uqikoj')
        self.assertEqual(choices[-1][1], 34)
        self.assertEqual(choices[-2][1], 34)
        self.assertTrue('koji' in (choices[-1][0].letters,
                                   choices[-2][0].letters))
        self.assertTrue('quoi' in (choices[-1][0].letters,
                                   choices[-2][0].letters))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(TestScrabbleHelper.sh._board)
    else:
        unittest.main()
