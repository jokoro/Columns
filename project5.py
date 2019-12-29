# Jason Okoro
# 13398381

import pygame
import columns
import random

SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400
BACKGROUND_COLOR = (82, 158, 66)

ROWS = 13
COLS = 6
FALLER_LENGTH = 3

FIELD_COLOR = (31, 66, 99)
FIELD_WIDTH = SCREEN_WIDTH * 0.25
FIELD_HEIGHT = FIELD_WIDTH * ROWS / COLS
FIELD_LEFT = (SCREEN_WIDTH - FIELD_WIDTH)/2
FIELD_TOP = (SCREEN_HEIGHT - FIELD_HEIGHT)/2
FIELD_RECT = pygame.Rect(FIELD_LEFT, FIELD_TOP, FIELD_WIDTH, FIELD_HEIGHT)

# red, green, blue, magenta, yellow, cyan, violet //  other candidates: (255, 122, 0) = orange
JEWEL_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255), (255, 255, 0), (255, 0, 255), (122, 0, 255)]
CELL_LINE_COLOR = BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

CELL_WIDTH = FIELD_WIDTH / COLS
CELL_HEIGHT = FIELD_HEIGHT / ROWS

NUM_FLASHES = 2


class ColumnsGame:
    def __init__(self):
        self._running = True
        self.game = columns.GameState(ROWS, COLS, self._empty_field(), FIELD_COLOR)
        self.surface = self._resize_surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

    def run_user_interface(self) -> None:
        """ Play Columns using a PyGame GUI. """
        pygame.init()

        self.clock.tick(1)

        while self._running:
            self._play_game()

        pygame.mixer.music.stop()
        pygame.quit()

    def _play_game(self) -> None:
        """
        Assuming field has contents in its field attribute, repeatedly takes a faller and repeats
        letting user alter it repeatedly and lowering it as time passes until it freezes, until
        a faller could not be fully displayed, in which case the game is over.
        """
        if self.game.game_is_over():  # in case made it all full at start
            self._display()
            self._end_game()

        if not self._running:
            return

        col = list(range(COLS))[int(random.random() * (COLS - .1))]
        while self.game.field[ROWS - 1][col].state != columns.EMPTY:  # only drop on non-full columns
            col = list(range(COLS))[int(random.random() * (COLS - .1))]

        faller_content = []
        for i in range(FALLER_LENGTH):
            faller_content += [JEWEL_COLORS[int(random.random() * (len(JEWEL_COLORS) - .1))]]

        self.game.initialize_faller(col + 1, faller_content)
        self._faller_falls_until_freezes()

        if not self._running:
            return

        self._clear_repeatedly()

        if self.game.game_is_over():
            self._end_game()

    def _faller_falls_until_freezes(self) -> None:
        """
        Get user to alter faller until they want to lower it, then lower it.
        Repeats this process until faller freezes.
        """
        while True:
            self.game.lower_faller()
            self.clock.tick(1)

            self._handle_events()
            if self._running:
                self._display()

            if not self._running:
                break

            if self.game.faller_froze:
                break

    def _handle_events(self) -> None:
        """ Get and use keyboard input to rotate or shift faller or to quit the game prematurely. """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._end_game()
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.game.shift_faller(-1)
                if event.key == pygame.K_RIGHT:
                    self.game.shift_faller(1)
                if event.key == pygame.K_SPACE:
                    self.game.rotate_faller()
            elif event.type == pygame.VIDEORESIZE:
                self.surface = self._resize_surface(event.size)

    def _clear_repeatedly(self) -> None:
        """ Clear matches, drop jewels above holes, and repeat. """
        while self.game.cells_might_match:
            self.game.prepare_to_clear()

            if self.game.matches_present():
                self._display()
            self.game.clear()
        self._display()
        self.clock.tick(1)

    def _empty_field(self) -> [[(int, int)]]:
        """ Return an empty field, i.e. a 2D list will all elements of a designated empty color. """
        contents = []
        for i in range(ROWS):
            row = []
            for j in range(COLS):
                row += [FIELD_COLOR]
            contents += [row]
        return contents[-1::-1]

    def _display(self) -> None:
        """ Displays what the field looks like now. """
        self.surface.fill(BACKGROUND_COLOR)
        pygame.draw.rect(self.surface, FIELD_COLOR, FIELD_RECT)

        cells_to_flash = []
        for i, row in enumerate(self.game.field[-1::-1]):
            for j, cell in enumerate(row):
                left = FIELD_LEFT + j * FIELD_WIDTH / COLS
                top = FIELD_TOP + i * FIELD_HEIGHT / ROWS
                points = ((left + FIELD_WIDTH / COLS, top + FIELD_HEIGHT / ROWS),
                          (left + FIELD_WIDTH / COLS, top), (left, top),
                          (left, top + FIELD_HEIGHT / ROWS))

                if cell.state == columns.LANDED or cell.state == columns.MATCH:
                    cells_to_flash += [(i, j)]  # cells_to_flash += [(left, top, points)]
                pygame.draw.rect(self.surface, cell.content, pygame.Rect(left, top, CELL_WIDTH, CELL_HEIGHT))
                pygame.draw.lines(self.surface, CELL_LINE_COLOR, True, points)

            pygame.display.flip()
        pygame.event.get()

        if cells_to_flash:
            for i in range(NUM_FLASHES * 2):
                self.clock.tick(7)
                for row, col in cells_to_flash:
                    left = FIELD_LEFT + col * FIELD_WIDTH / COLS
                    top = FIELD_TOP + row * FIELD_HEIGHT / ROWS
                    points = ((left + FIELD_WIDTH / COLS, top + FIELD_HEIGHT / ROWS),
                              (left + FIELD_WIDTH / COLS, top), (left, top),
                              (left, top + FIELD_HEIGHT / ROWS))

                    if i % 2 == 0:
                        pygame.draw.rect(self.surface, WHITE, pygame.Rect(left, top, CELL_WIDTH, CELL_HEIGHT))
                        pygame.draw.lines(self.surface, CELL_LINE_COLOR, True, points)
                    else:
                        pygame.draw.rect(self.surface, self.game.field[-1::-1][row][col].content,
                                         pygame.Rect(left, top, CELL_WIDTH, CELL_HEIGHT))
                        pygame.draw.lines(self.surface, CELL_LINE_COLOR, True, points)
                pygame.display.flip()
                self._handle_events()
                
    def _resize_surface(self, size: (int, int)) -> pygame.Surface:
        """ Return a resizable surface. """
        return pygame.display.set_mode(size, pygame.RESIZABLE)

    def _end_game(self) -> None:
        """ Set _running to False to end the game. """
        self._running = False


if __name__ == '__main__':
    ColumnsGame().run_user_interface()
