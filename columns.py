# Jason Okoro
# 13398381

import random

EMPTY = 0  # EMPTY implies it's not a jewel, but the rest imply it is
FALLING = 1
LANDED = 2
FROZEN = 3
MATCH = 4

MIN_TO_MATCH = 3


class NotEnoughContentError(Exception):
    pass


class GameOverError(Exception):
    pass


class InvalidFieldSizeError(Exception):
    pass


class FieldCell:  # class to describe jewels and empty field cells
    def __init__(self, content, state: int) -> None:
        self.content = content
        self.state = state


class GameState:
    def __init__(self, rows, cols, contents, empty_content) -> None:
        if rows <= 0 or cols <= 0:
            raise InvalidFieldSizeError('Field cannot be empty.')

        self._rows = rows
        self._cols = cols
        self._empty_content = empty_content

        self.field = []
        self._field_extension = []  # where invisible cells lay, convenient for matching then returning field to user

        self._faller = []
        self._faller_row = 0
        self._faller_col = 0

        self.cells_might_match = []
        self._matches_present = False
        self.faller_froze = False
        self._just_cleared = True

        self.create_field(contents)

    def get_rows(self) -> int:
        """ Return _rows. """
        return self._rows

    def get_cols(self) -> int:
        """ Return _cols. """
        return self._cols

    def matches_present(self) -> bool:
        """ Return _matches_present. True if checked for matches and found at least one, False otherwise. """
        return self._matches_present

    def create_field(self, contents: [[]]) -> None:
        """ Creates a field with predetermined contents with _rows number of rows, and _cols number of columns. """
        self.cells_might_match = []

        for row in range(self._rows):
            row_list = []
            for col in range(self._cols):
                try:
                    if contents[row][col] == self._empty_content:
                        row_list += [FieldCell(contents[row][col], EMPTY)]
                    else:
                        row_list += [FieldCell(contents[row][col], FROZEN)]
                        self.cells_might_match += [(row, col)]
                except IndexError:
                    raise InvalidFieldSizeError('Either not enough rows or not enough columns in some row in contents.')
            self.field += [row_list]
        self._drop_all_jewels()

    def prepare_to_clear(self) -> None:
        """ Uses cells_might_match as a starting point to find matches in field and tags them with MATCH. """
        if self.game_is_over():
            raise GameOverError('Cannot modify field. Game is over.')

        self.field += self._field_extension
        self._matches_present = False

        for row, col in self.cells_might_match:
            for row_del, col_del in [(0, 1), (1, 0), (1, 1), (1, -1)]:  # different "angles"
                cells_in_match = []
                for i in [1, -1]:  # opposite directions along angles
                    j = 0

                    while True:
                        current_row = row + i * j * row_del
                        current_col = col + i * j * col_del

                        next_row = row + i * (j + 1) * row_del
                        next_col = col + i * (j + 1) * col_del

                        if 0 > next_row or next_row > len(self.field) - 1 or 0 > next_col or next_col > self._cols - 1 \
                                or self.field[current_row][current_col].content != self.field[next_row][next_col].content:
                            break

                        cells_in_match.insert(len(cells_in_match) - 1, (current_row, current_col))
                        cells_in_match += [(next_row, next_col)]
                        j += 1

                if len(cells_in_match) >= MIN_TO_MATCH:
                    self._matches_present = True
                    for row, col in cells_in_match:
                        if self.field[row][col].state != EMPTY:
                            self.field[row][col].state = MATCH

        self.cells_might_match = []
        self._detach_field_extension()

    def clear(self) -> None:
        """ Removes jewels tagged with MATCH and drops jewels over holes. """
        if self.game_is_over():
            raise GameOverError('Cannot modify field. Game is over.')

        self.field += self._field_extension
        for row in range(len(self.field)):
            for col in range(self._cols):
                if self.field[row][col].state == MATCH:
                    self.field[row][col] = FieldCell(self._empty_content, EMPTY)
        self._drop_all_jewels()
        self._detach_field_extension()
        self._just_cleared = True

    def initialize_faller(self, col, faller_content) -> None:
        """ Initialize faller content and its column randomly with bottom position at top of field. """
        if self.game_is_over():
            raise GameOverError('Cannot modify faller. Game is over.')

        self.faller_froze = False
        self._faller_row = len(self.field)
        self._faller_col = col - 1

        self._faller = []
        for content in faller_content:
            if self.faller_landed():
                self._faller += [FieldCell(content, LANDED)]
            else:
                self._faller += [FieldCell(content, FALLING)]

        self._initialize_field_extension()

    def lower_faller(self) -> None:
        """ Move faller down in the field and update _field_extension. """
        if self.game_is_over():
            raise GameOverError('Cannot modify faller. Game is over.')

        self._erase_faller_from_field()

        if self._faller[0].state == LANDED and self.faller_landed():
            self._set_faller_state(FROZEN)
            self.faller_froze = True

            for i in range(len(self._faller)):
                self.cells_might_match += [(self._faller_row + i, self._faller_col)]
        else:
            self._faller_row -= 1
            if self.faller_landed():
                self._set_faller_state(LANDED)
            else:
                self._set_faller_state(FALLING)

        self._add_faller_to_field()

    def rotate_faller(self) -> None:
        """ Rotate faller. """
        if self.game_is_over():
            raise GameOverError('Cannot modify faller. Game is over.')

        # no need to erase, overwrites its old one
        for row_idx in range(len(self._faller)):
            if row_idx == 0:
                temp = self._faller[row_idx]
                self._faller[row_idx] = self._faller[row_idx + 1]
            elif row_idx == len(self._faller) - 1:
                self._faller[row_idx] = temp
            else:
                self._faller[row_idx] = self._faller[row_idx + 1]

        self._add_faller_to_field()

    def shift_faller(self, col_del: int) -> None:
        """
        Move faller left or right. If col_del < 0, goes left, > 0 goes right,
        0 stays the same. Moves |col_del| columns in either direction unless
        there is a wall or a jewel in the position it will move to.
        """
        if self.game_is_over():
            raise GameOverError('Cannot modify faller. Game is over.')

        self._erase_faller_from_field()

        if 0 <= self._faller_col + col_del < self._cols \
                and self.field[self._faller_row][self._faller_col + col_del].state == EMPTY:
            self._faller_col += col_del

        self._add_faller_to_field()

    def game_is_over(self) -> bool:
        """
        Returns True if the game is over (meaning a faller could not be
        fully placed in field despite any matches that may have happened), False otherwise.
        """
        all_cells_frozen = True
        field_extension_not_empty = False
        top_row_full = True

        done = False
        for row in self._field_extension:
            for cell in row:
                if cell.state != EMPTY:
                    field_extension_not_empty = True
                    done = True
                    break
            if done:
                break

        done = False
        for row in self.field:
            for cell in row:
                if cell.state not in {FROZEN, EMPTY}:
                    all_cells_frozen = False
                    done = True
                    break
            if done:
                break

        for cell in self.field[len(self.field) - 1]:
            if cell.state == EMPTY:
                top_row_full = False
                break

        if self._just_cleared and (all_cells_frozen and field_extension_not_empty or top_row_full):
            self._just_cleared = False
            return True
        else:
            self._just_cleared = False
            return False

    def _drop_all_jewels(self) -> None:
        """
        Drops any jewels in field above holes down so each column only
        has one stack of jewels and that it touches the bottom. Then anticipates matches.
        """
        for col_idx in range(self._cols):
            for row_idx in range(len(self.field) - 1):
                if self.field[row_idx][col_idx].state == EMPTY:
                    for row_idx2 in range(row_idx + 1, len(self.field)):
                        if self.field[row_idx2][col_idx].state != EMPTY:
                            self.field[row_idx][col_idx] = self.field[row_idx2][col_idx]
                            self.field[row_idx2][col_idx] = FieldCell(self._empty_content, EMPTY)
                            self.cells_might_match += [(row_idx, col_idx)]
                            break

    def _initialize_field_extension(self) -> None:
        """ Initialize _field_extension, the invisible part above the field, using faller. """
        self._field_extension = []

        for i in range(len(self._faller)):
            row = []
            for j in range(self._cols):
                if j == self._faller_col:
                    row += [self._faller[i]]
                else:
                    row += [FieldCell(self._empty_content, EMPTY)]
            self._field_extension += [row]

    def _detach_field_extension(self) -> None:
        """ Removes _field_extension from field. """
        for i in range(len(self._field_extension)):
            self.field.pop()

    def faller_landed(self) -> None:
        """ Return True if below faller is the floor or a jewel, False otherwise. """
        return self._faller_row == 0 or self.field[self._faller_row - 1][self._faller_col].state != EMPTY

    def _set_faller_state(self, state):
        """ Set the FieldCell state for each cell in faller using state. """
        for i in range(len(self._faller)):
            self._faller[i].state = state

    def _add_faller_to_field(self) -> None:
        """ Add faller to the field and _field_extension, depending on _faller_row (bottom cell) and _faller_col. """
        self.field += self._field_extension

        if self._faller[0].state != FROZEN:
            if self.faller_landed():
                self._set_faller_state(LANDED)
            else:
                self._set_faller_state(FALLING)

        for i in range(len(self._faller)):
            self.field[self._faller_row + i][self._faller_col] = self._faller[i]

        self._detach_field_extension()

    def _erase_faller_from_field(self) -> None:
        """ Remove faller from the field and _field_extension, wherever it is. """
        self.field += self._field_extension

        for i in range(len(self._faller)):
            self.field[self._faller_row + i][self._faller_col] = FieldCell(self._empty_content, EMPTY)

        self._detach_field_extension()
