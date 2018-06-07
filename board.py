"""
    This class defines an immutable scrabble board. This includes marked "special"
    squares, and letter played to the board. This board is ignorant of to which
    player the pieces belongs.
"""
import enum
import unittest
import itertools
from collections import defaultdict, namedtuple

BOARD_SIDE = 15
Piece = namedtuple('Piece', ['letter', 'is_blank'])

class Colors(enum.Enum):
    green = '\033[32m'
    red = '\033[91m'
    end = '\033[0m'

    @staticmethod
    def encode(color, message):
        return color.value + message + Colors.end.value

class SpotType(enum.Enum):
    normal = '    '
    double_letter = '<dl>'
    triple_letter = '<tl>'
    double_word = '<dw>'
    triple_word = '<tw>'

def set_rotate(quad0):
    move_left = lambda x: (14 - x[0], x[1])
    move_up = lambda x: (x[0], 14 - x[1])
    move_diag = lambda x: move_left(move_up(x))
    return tuple(set(quad0).union(map(move_left, quad0))
                 .union(map(move_up, quad0))
                 .union(map(move_diag, quad0)))

def set_flip(eighth1):
    return tuple(set(eighth1).union(map(lambda x: (x[1], x[0]), eighth1)))

def get_board():
    dd = {(i, j): SpotType.normal for j in range(15) for i in range(15)}
    dl = set_rotate(set_flip(((3, 0), (6, 2), (7, 3), (6, 6))))
    tl = set_rotate(set_flip(((5, 1), (5, 5))))
    dw = set_rotate(tuple((i, i) for i in range(1, 5)) + ((7, 7),))
    tw = set_rotate(((0, 0), (7, 0), (0, 7)))
    dd.update({k: SpotType.double_letter for k in dl})
    dd.update({k: SpotType.triple_letter for k in tl})
    dd.update({k: SpotType.double_word for k in dw})
    dd.update({k: SpotType.triple_word for k in tw})
    return dd

class ScrabbleBoard(object):
    board_config = get_board()

    def __init__(self, pieces={}):
        self._board = self.board_config
        self._pieces = pieces
        self._hash = hash(frozenset(self._pieces.items()))

    @classmethod
    def from_pieces(cls, pieces):
        return cls(pieces)

    def _safe_piece(self, loc, letter, is_blank):
        piece = Piece(letter.lower(), is_blank)
        assert letter.isalpha(), 'Only words with alphabetic characters'
        assert loc[0] >= 0 and loc[0] <= 14 and loc[1] >= 0 and loc[1] <= 14, \
            'Location out of bounds'
        assert ((loc not in self._pieces) or (piece == self._pieces[loc])), \
            'Conflict with already placed piece'
        return piece

    # Not sure the use case of this
    def place_piece(self, location, letter, is_blank=False):
        new_peices = self._pieces.copy()
        new_peices[location] = self._safe_piece(location, letter, is_blank)
        return self.from_pieces(new_peices)

    def place_word(self, word, start_location, vertical=False, blanks=()):
        new_peices = self._pieces.copy()
        for offset, letter in enumerate(word):
            loc = (start_location[0], start_location[1] - offset) if vertical \
                else (start_location[0] + offset, start_location[1])
            new_peices[loc] = self._safe_piece(loc, letter, offset in blanks)
        return self.from_pieces(new_peices)

    def consider_play(self, play):
        new_peices = self._pieces.copy()
        start = play.location
        next_loc = lambda l: (l[0], l[1] - 1) if \
            play.vertical else (l[0] + 1, l[1])
        for letter in play.letters:
            while self[start][1] is not None:
                start = next_loc(start)
            new_peices[start] = Piece(Colors.encode(Colors.red, letter), False)
            start = next_loc(start)
        return self.from_pieces(new_peices)

    @property
    def open_tiles(self):
        return filter(lambda x: x not in self._pieces, self._board.keys())

    def __getitem__(self, location):
        return self._board[location], self._pieces.get(location)

    def __hash__(self):
        return self._hash

    # TODO: Needs tests
    def __eq__(self, other):
        return hash(self) == hash(other) and self._pieces == other._pieces

    def _spot_repr(self, location):
        tile_val, piece = self[location]
        return (' {}{} '.format(piece.letter, '*' if piece.is_blank else ' ')
                if piece else tile_val.value)

    def __repr__(self):
        return '\n'.join(
            ('|'.join(self._spot_repr((i, j)) for i in range(15)))
            for j in reversed(range(15)))


class TestScrabbleBoard(unittest.TestCase):
    def expect_assertion(self, f, reverse=False):
        try:
            f()
            self.assertTrue(reverse)
        except:
            self.assertTrue(not reverse)

    def setUp(self):
        self.sb = ScrabbleBoard()

    def test_bounds(self):
        sb = self.sb
        bounds = lambda loc, is_good: \
            self.expect_assertion(lambda: sb.place_piece(loc, 'a'), is_good)

        for loc in itertools.product(range(-5, 20), repeat=2):
            bounds(loc, (loc[0] in range(15)) and (loc[1] in range(15)))

    def test_play_words(self):
        sb = self.sb
        sb = (sb.place_word('hello', (7, 7))
              .place_word('orange', (11, 7), vertical=True)
              # Mark 'd' as blank
              .place_word('edge', (11, 2), blanks=(1,)))
        self.assertEqual(len(sb._pieces), (len('hello') + len('orange')
                                           + len('edge') - 2))
        # Try overwrite the 'd' in edge with another blank 'd', then a
        # non-blank one
        sb = sb.place_piece((12, 2), 'd', is_blank=True)
        self.expect_assertion(lambda: sb.place_piece((12, 2), 'd',
                                                     is_blank=False))
        # Run one off the bottom of board
        self.expect_assertion(lambda: sb.place_word('eels', (14, 2),
                                                    vertical=True))
        # Hit the bottom right corner going down
        sb = sb.place_word('eel', (14, 2), vertical=True)
        sb = sb.place_word('feel', (14, 3), vertical=True)
        # This should change 'f' at (14, 3) to a p
        self.expect_assertion(lambda: sb.place_word('peel', (14, 3),
                                                    vertical=True))
        self.sb = sb # For test_repr

    def test_play_piece(self):
        sb_o = sb = self.sb
        location_letter_iter = zip(
            itertools.product(range(BOARD_SIDE), repeat=2),
            itertools.cycle(map(lambda l: chr(ord('a') + l), range(25))))
        # Try to add invalid piece
        self.expect_assertion(lambda: sb.place_piece('$', (5, 5)))
        # Add piece to every spot on board (letter a-y)
        for loc, letter in location_letter_iter:
            sb = sb.place_piece(loc, letter)
        # There should be 15 * 15 pieces on board now
        self.assertEqual(len(sb._pieces), BOARD_SIDE ** 2)
        # Try to add another piece which is not the same as the one played
        self.expect_assertion(lambda: sb.place_piece((7, 7), 'z'))
        # Add an 'a' again to (0, 0)
        sb.place_piece((0, 0), 'a')
        # Go over sb with same iterator and check that the letters are really
        # there, and that sb_o has nothing there
        for loc, letter in location_letter_iter:
            orig_spot, orig_piece = sb_o[location]
            full_spot, full_piece = sb[location]
            self.assertEqual(orig_spot, full_spot)
            self.assertEqual(orig_piece, None)
            self.assertEqual(full_piece, Piece(letter=letter, is_blank=False))

    def test_repr(self):
        self.test_play_words()
        repr_ = repr(self.sb)
        repr_split = repr_.split('\n')
        # 15 lines is the hight of a scrabble board
        self.assertEqual(len(repr_split), 15)
        # Each tile horizontally is represented by 4 characters, and separated
        # by 1
        self.assertTrue(all(len(line) == 4 * 15 + 14 for line in repr_split))

    @classmethod
    def tearDownClass(cls):
        # Hack to get a board to show up AFTER all the tests
        t = cls()
        t.setUp()
        t.test_play_words()
        print(' Example board:')
        print(t.sb)

if __name__ == '__main__':
    unittest.main()
