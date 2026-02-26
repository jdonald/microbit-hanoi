"""
Tower of Hanoi game logic for micro:bit V2.

No hardware dependencies - suitable for unit testing on PC.

World layout:
  - 15 columns wide, 3 pegs at world columns 2, 7, 12
  - 5-wide view window, scroll range 0-10
  - Blocks 1-4 have LED widths 1, 3, 5, 7
  - 7-wide block overflow wraps to the row above

Display rows:
  - Row 0: held block (always on-screen, blinks)
  - Rows 1-4: game area (sticks + stacked blocks)
"""

# Block number -> LED width mapping (index 0 unused)
BLOCK_WIDTHS = [0, 1, 3, 5, 7]

# World layout
WORLD_WIDTH = 15
PEG_COLS = [2, 7, 12]   # world column of each peg (left, middle, right)
NUM_PEGS = 3
SCREEN_WIDTH = 5
SCREEN_HEIGHT = 5
MAX_SCROLL = WORLD_WIDTH - SCREEN_WIDTH  # = 10
SCREEN_CENTER_COL = SCREEN_WIDTH // 2   # = 2

# Display rows
HELD_ROW = 0
PEG_ROW_TOP = 1
PEG_ROW_BOTTOM = 4

# Brightness values (0-9)
BRIGHTNESS_BLOCK = 9
BRIGHTNESS_STICK = 5
BRIGHTNESS_HELD = 7


class GameState:
    """Complete mutable game state for Tower of Hanoi."""

    def __init__(self):
        self.level = 1
        self.pegs = [[], [], []]
        self.held_block = None      # block number currently held, or None
        self.held_from_peg = None   # peg index the held block came from
        self.scroll = 0.0           # fractional horizontal scroll offset
        self.setup_level()

    def setup_level(self):
        """Initialise blocks for the current level on the leftmost peg."""
        n = self.level
        # Stack: index 0 = largest block (bottom), index -1 = smallest (top)
        self.pegs = [list(range(n, 0, -1)), [], []]
        self.held_block = None
        self.held_from_peg = None
        self.scroll = 0.0

    @property
    def scroll_int(self):
        """Integer scroll offset used for pixel rendering."""
        return int(self.scroll)

    def get_selected_peg(self):
        """Return index of the peg closest to the screen centre."""
        centre = self.scroll + SCREEN_CENTER_COL
        best_idx = 0
        best_dist = abs(PEG_COLS[0] - centre)
        for i in range(1, NUM_PEGS):
            d = abs(PEG_COLS[i] - centre)
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx

    def action(self):
        """Right button: pick up top block from selected peg, or place held block.

        Returns True when the action succeeds (pick-up from non-empty peg,
        or legal placement).
        """
        peg_idx = self.get_selected_peg()
        if self.held_block is None:
            # Pick up the top block
            if not self.pegs[peg_idx]:
                return False
            self.held_block = self.pegs[peg_idx].pop()
            self.held_from_peg = peg_idx
            return True
        else:
            # Place the held block (only if peg is empty or top block is larger)
            top = self.pegs[peg_idx][-1] if self.pegs[peg_idx] else None
            if top is None or top > self.held_block:
                self.pegs[peg_idx].append(self.held_block)
                self.held_block = None
                self.held_from_peg = None
                return True
            return False  # invalid: cannot place a larger block on a smaller one

    def cancel(self):
        """Left button: return the held block to its source peg (no-op if nothing held)."""
        if self.held_block is not None:
            self.pegs[self.held_from_peg].append(self.held_block)
            self.held_block = None
            self.held_from_peg = None

    def is_level_complete(self):
        """True when all blocks are on the rightmost peg and nothing is held."""
        return len(self.pegs[2]) == self.level and self.held_block is None

    def next_level(self):
        """Advance to the next level, wrapping back to 1 after level 4."""
        self.level = (self.level % 4) + 1
        self.setup_level()

    def update_scroll(self, accel_x, dt_ms):
        """Update scroll position from an accelerometer X reading.

        accel_x : micro:bit accelerometer X value, approximately -1024 to +1024
                  (positive = right side lower, negative = left side lower)
        dt_ms   : elapsed time in milliseconds since last call

        Tilting left  (accel_x < 0) scrolls right (view offset increases).
        Tilting right (accel_x > 0) scrolls left  (view offset decreases).
        Larger tilt magnitude scrolls faster.
        """
        # At maximum tilt (1024), traverse the full scroll range (10 units) in 2 s.
        scale = 10.0 / (1024.0 * 2000.0)
        delta = -accel_x * scale * dt_ms
        self.scroll = max(0.0, min(float(MAX_SCROLL), self.scroll + delta))


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_frame(game_state, stick_on=True, held_on=True):
    """Render the game state to a 5×5 brightness grid.

    Args:
        game_state : GameState instance
        stick_on   : whether sticks are lit this blink phase
        held_on    : whether the held block is lit this blink phase

    Returns:
        list[list[int]] – 5 rows × 5 columns, brightness values 0-9.
    """
    grid = [[0] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
    scroll = game_state.scroll_int

    # Draw sticks (faded via blinking controlled by stick_on)
    if stick_on:
        for peg_col in PEG_COLS:
            sc = peg_col - scroll
            if 0 <= sc < SCREEN_WIDTH:
                for row in range(PEG_ROW_TOP, SCREEN_HEIGHT):
                    _set_pixel(grid, row, sc, BRIGHTNESS_STICK)

    # Draw placed blocks (always lit, override stick pixels)
    for peg_idx in range(NUM_PEGS):
        peg_col = PEG_COLS[peg_idx]
        stack = game_state.pegs[peg_idx]
        for depth, block_num in enumerate(stack):
            row = PEG_ROW_BOTTOM - depth
            _draw_world_block(grid, block_num, peg_col, row, scroll, BRIGHTNESS_BLOCK)

    # Draw held block centred at top of screen, unaffected by scroll
    if game_state.held_block is not None and held_on:
        _draw_screen_block(grid, game_state.held_block,
                           HELD_ROW, SCREEN_CENTER_COL, BRIGHTNESS_HELD)

    return grid


def _set_pixel(grid, row, col, brightness):
    """Write brightness to grid[row][col] if in-bounds and higher than current."""
    if 0 <= row < SCREEN_HEIGHT and 0 <= col < SCREEN_WIDTH:
        if grid[row][col] < brightness:
            grid[row][col] = brightness


def _draw_world_block(grid, block_num, world_col, row, scroll, brightness):
    """Draw a block in world coordinates.

    Pixels that overflow the left or right screen edge wrap upward to the
    row above (the '7-LEDs bend around the top' effect).
    """
    if not (1 <= block_num <= 4):
        return
    half = BLOCK_WIDTHS[block_num] // 2
    for dc in range(-half, half + 1):
        sc = world_col + dc - scroll
        if 0 <= sc < SCREEN_WIDTH:
            _set_pixel(grid, row, sc, brightness)
        elif row > HELD_ROW:
            # Overflow: wrap horizontally into the row above
            if sc < 0:
                _set_pixel(grid, row - 1, sc + SCREEN_WIDTH, brightness)
            else:  # sc >= SCREEN_WIDTH
                _set_pixel(grid, row - 1, sc - SCREEN_WIDTH, brightness)


def _draw_screen_block(grid, block_num, row, centre_sc, brightness):
    """Draw a block in screen coordinates (clipped, no wrapping)."""
    if not (1 <= block_num <= 4):
        return
    half = BLOCK_WIDTHS[block_num] // 2
    for dc in range(-half, half + 1):
        _set_pixel(grid, row, centre_sc + dc, brightness)
