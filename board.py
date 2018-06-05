"""
    This class defines an immutable scrabble board. This includes marked "special"
    squares, and letter played to the board. This board is ignorant of to which
    player the pieces belongs.
"""
import enum
from collections import defaultdict, namedtuple

Piece = namedtuple('Piece', ['letter', 'is_blank'])

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

    @classmethod
    def from_pieces(cls, pieces):
        return cls(pieces)

    def bounds_check(self, loc):
        assert loc[0] >= 0 and loc[0] <= 14 and loc[1] >= 0 and loc[1] <= 14, \
            'Location out of bounds'

    def place_piece(self, location, letter, is_blank=False):
        # Maybe this should be turned of if trying to play the same piece
        assert location not in self._pieces, 'Playing over another piece'
        self.bounds_check(location)
        new_peices = self._pieces.copy()
        new_peices[location] = Piece(letter, is_blank)
        return self.from_pieces(new_peices)

    # TODO: Needs bounds checking
    def place_word(self, word, start_location, vertical=False, blanks=()):
        new_peices = self._pieces.copy()
        for offset, letter in enumerate(word):
            loc = (start_location[0], start_location[1] - offset) if vertical \
                else (start_location[0] + offset, start_location[1]) 
            self.bounds_check(loc)
            piece = Piece(letter, offset in blanks)
            if loc in new_peices:
                assert piece == new_peices[loc], 'Word conflicts with ' \
                    'already placed piece'
            else:
                new_peices[loc] = piece
        return self.from_pieces(new_peices)


    def __getitem__(self, location):
        return self._board[location], self._pieces.get(location)

    def _spot_repr(self, location):
        tile_val, piece = self[location]
        return (' {}{} '.format(piece.letter, '*' if piece.is_blank else ' ')
                if piece else tile_val.value)

    def __repr__(self):
        return '\n'.join(
            ('|'.join(self._spot_repr((i, j)) for i in range(15))) 
            for j in reversed(range(15)))
