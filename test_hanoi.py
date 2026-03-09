"""
Unit tests for hanoi_logic.py.

Run with:  pytest test_hanoi.py
No hardware required – pure Python only.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from hanoi_logic import (
    GameState, render_frame, compute_layout,
    BLOCK_WIDTHS,
    BRIGHTNESS_BLOCK, BRIGHTNESS_STICK, BRIGHTNESS_HELD,
    HELD_ROW, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_CENTER_COL,
    PEG_ROW_TOP, PEG_ROW_BOTTOM, NUM_PEGS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_game(level=1, scroll=0.0):
    g = GameState()
    g.level = level
    g.setup_level()
    g.scroll = scroll
    return g


def peg_scroll(game, peg_idx):
    """Scroll value that exactly centres peg_idx on the screen."""
    return float(game.peg_cols[peg_idx] - SCREEN_CENTER_COL)


def grid_str(grid):
    return "\n" + "\n".join(" ".join(str(v) for v in row) for row in grid)


# ---------------------------------------------------------------------------
# compute_layout
# ---------------------------------------------------------------------------

class TestComputeLayout:
    def test_peg0_always_at_col2(self):
        for level in range(1, 5):
            peg_cols, _, _ = compute_layout(level)
            assert peg_cols[0] == 2, f"level {level}"

    def test_separation_equals_2_times_level(self):
        for level in range(1, 5):
            peg_cols, _, _ = compute_layout(level)
            sep = 2 * level
            assert peg_cols[1] - peg_cols[0] == sep
            assert peg_cols[2] - peg_cols[1] == sep

    def test_max_scroll_centres_peg2(self):
        """At max_scroll, peg2 lands on screen centre column."""
        for level in range(1, 5):
            peg_cols, _, max_scroll = compute_layout(level)
            assert peg_cols[2] - max_scroll == SCREEN_CENTER_COL

    def test_world_width_covers_scroll_range(self):
        for level in range(1, 5):
            _, world_width, max_scroll = compute_layout(level)
            assert world_width == max_scroll + SCREEN_WIDTH

    def test_level1_values(self):
        peg_cols, world_width, max_scroll = compute_layout(1)
        assert peg_cols == [2, 4, 6]
        assert max_scroll == 4
        assert world_width == 9

    def test_level2_values(self):
        peg_cols, world_width, max_scroll = compute_layout(2)
        assert peg_cols == [2, 6, 10]
        assert max_scroll == 8

    def test_level4_values(self):
        peg_cols, world_width, max_scroll = compute_layout(4)
        assert peg_cols == [2, 10, 18]
        assert max_scroll == 16

    def test_no_block_overlap_between_pegs(self):
        """Widest block on adjacent pegs must not share a world column."""
        for level in range(1, 5):
            peg_cols, _, _ = compute_layout(level)
            half = BLOCK_WIDTHS[level] // 2
            # Right edge of block on peg0, left edge of block on peg1
            right0 = peg_cols[0] + half
            left1 = peg_cols[1] - half
            assert right0 < left1, \
                f"level {level}: overlap between peg0 and peg1"


# ---------------------------------------------------------------------------
# GameState – initialisation
# ---------------------------------------------------------------------------

class TestSetup:
    def test_initial_level_is_1(self):
        assert GameState().level == 1

    def test_level1_has_one_block_on_peg0(self):
        g = make_game(level=1)
        assert g.pegs[0] == [1]
        assert g.pegs[1] == []
        assert g.pegs[2] == []

    def test_level2_stack_ordering(self):
        # largest at index 0 (bottom), smallest at -1 (top)
        assert make_game(level=2).pegs[0] == [2, 1]

    def test_level3_stack_ordering(self):
        assert make_game(level=3).pegs[0] == [3, 2, 1]

    def test_level4_stack_ordering(self):
        assert make_game(level=4).pegs[0] == [4, 3, 2, 1]

    def test_initial_scroll_is_zero(self):
        assert GameState().scroll == 0.0

    def test_no_held_block_initially(self):
        assert GameState().held_block is None

    def test_peg_cols_set_by_setup(self):
        g = make_game(level=1)
        assert g.peg_cols == [2, 4, 6]

    def test_max_scroll_set_by_setup(self):
        g = make_game(level=2)
        _, _, expected = compute_layout(2)
        assert g.max_scroll == expected

    def test_setup_level_resets_scroll(self):
        g = GameState()
        g.scroll = 7.5
        g.setup_level()
        assert g.scroll == 0.0

    def test_setup_level_resets_held(self):
        g = GameState()
        g.held_block = 1
        g.held_from_peg = 0
        g.setup_level()
        assert g.held_block is None
        assert g.held_from_peg is None

    def test_setup_updates_layout_for_new_level(self):
        g = GameState()
        g.level = 3
        g.setup_level()
        assert g.peg_cols == compute_layout(3)[0]
        assert g.max_scroll == compute_layout(3)[2]


# ---------------------------------------------------------------------------
# Peg selection from scroll position
# ---------------------------------------------------------------------------

class TestPegSelection:
    def test_scroll_0_always_selects_peg0(self):
        # peg0 is always at col 2 = screen centre at scroll 0
        for level in range(1, 5):
            g = make_game(level=level, scroll=0.0)
            assert g.get_selected_peg() == 0, f"level {level}"

    def test_peg1_selected_at_correct_scroll(self):
        for level in range(1, 5):
            g = make_game(level=level)
            g.scroll = peg_scroll(g, 1)
            assert g.get_selected_peg() == 1, f"level {level}"

    def test_peg2_selected_at_max_scroll(self):
        for level in range(1, 5):
            g = make_game(level=level)
            g.scroll = float(g.max_scroll)
            assert g.get_selected_peg() == 2, f"level {level}"

    def test_selection_favours_closer_peg(self):
        g = make_game(level=2)   # pegs at 2, 6, 10; sep=4
        # scroll=1: centre=3, dist to peg0(2)=1, dist to peg1(6)=3 → peg0
        g.scroll = 1.0
        assert g.get_selected_peg() == 0
        # scroll=3: centre=5, dist to peg0=3, dist to peg1=1 → peg1
        g.scroll = 3.0
        assert g.get_selected_peg() == 1

    def test_max_scroll_selects_peg2_all_levels(self):
        for level in range(1, 5):
            g = make_game(level=level)
            g.scroll = float(g.max_scroll)
            assert g.get_selected_peg() == 2


# ---------------------------------------------------------------------------
# Pick-up action
# ---------------------------------------------------------------------------

class TestPickUp:
    def test_pick_up_from_nonempty_peg_succeeds(self):
        g = make_game(level=1, scroll=0.0)
        assert g.action() is True

    def test_picked_up_block_removed_from_peg(self):
        g = make_game(level=1, scroll=0.0)
        g.action()
        assert g.pegs[0] == []

    def test_held_block_set_after_pickup(self):
        g = make_game(level=1, scroll=0.0)
        g.action()
        assert g.held_block == 1

    def test_held_from_peg_recorded(self):
        g = make_game(level=1, scroll=0.0)
        g.action()
        assert g.held_from_peg == 0

    def test_pick_up_from_empty_peg_fails(self):
        g = make_game(level=1)
        g.scroll = peg_scroll(g, 1)   # peg 1 is empty
        assert g.action() is False
        assert g.held_block is None

    def test_pick_up_top_block_from_two_block_stack(self):
        g = make_game(level=2, scroll=0.0)   # pegs[0] = [2, 1]
        g.action()
        assert g.held_block == 1
        assert g.pegs[0] == [2]

    def test_right_button_while_holding_tries_to_place(self):
        g = make_game(level=2, scroll=0.0)
        g.action()                  # pick up block 1
        assert g.held_block == 1
        # Press again on same peg (block 2 at top → larger → legal)
        result = g.action()
        assert result is True
        assert g.held_block is None
        assert g.pegs[0] == [2, 1]


# ---------------------------------------------------------------------------
# Placement action
# ---------------------------------------------------------------------------

class TestPlace:
    def test_place_on_empty_peg(self):
        g = make_game(level=1, scroll=0.0)
        g.action()                      # pick up block 1
        g.scroll = peg_scroll(g, 1)
        assert g.action() is True
        assert g.pegs[1] == [1]
        assert g.held_block is None

    def test_place_smaller_on_larger_succeeds(self):
        g = make_game(level=2, scroll=0.0)
        g.action()                      # pick up block 1
        g.scroll = peg_scroll(g, 1)
        g.action()                      # place block 1 on peg 1
        g.scroll = peg_scroll(g, 0)
        g.action()                      # pick up block 2
        g.scroll = peg_scroll(g, 2)
        assert g.action() is True
        assert g.pegs[2] == [2]

    def test_place_larger_on_smaller_fails(self):
        g = make_game(level=2, scroll=0.0)
        g.action()                      # pick up block 1
        g.scroll = peg_scroll(g, 1)
        g.action()                      # place block 1 on peg 1
        g.scroll = peg_scroll(g, 0)
        g.action()                      # pick up block 2
        g.scroll = peg_scroll(g, 1)    # peg 1 has block 1 on top
        result = g.action()             # illegal: block 2 on block 1
        assert result is False
        assert g.held_block == 2
        assert g.pegs[1] == [1]

    def test_place_block_back_on_source_peg(self):
        g = make_game(level=2, scroll=0.0)
        g.action()                      # pick up block 1
        result = g.action()             # put back (block 2 is larger → legal)
        assert result is True
        assert g.pegs[0] == [2, 1]
        assert g.held_block is None


# ---------------------------------------------------------------------------
# Cancel action
# ---------------------------------------------------------------------------

class TestCancel:
    def test_cancel_returns_block_to_source(self):
        g = make_game(level=1, scroll=0.0)
        g.action()
        g.cancel()
        assert g.held_block is None
        assert g.pegs[0] == [1]

    def test_cancel_when_nothing_held_is_noop(self):
        g = make_game(level=1)
        g.cancel()
        assert g.held_block is None

    def test_cancel_restores_after_scrolling_away(self):
        g = make_game(level=2, scroll=0.0)
        g.action()                      # pick up block 1 from peg 0
        g.scroll = float(g.max_scroll)  # scroll far away
        g.cancel()
        assert g.pegs[0] == [2, 1]
        assert g.held_block is None

    def test_cancel_with_multi_block_pickup(self):
        g = make_game(level=3, scroll=0.0)
        # Move block 1 to peg 1
        g.action()
        g.scroll = peg_scroll(g, 1)
        g.action()
        # Pick up block 2 from peg 0
        g.scroll = peg_scroll(g, 0)
        g.action()
        assert g.held_block == 2
        g.cancel()
        assert g.pegs[0] == [3, 2]


# ---------------------------------------------------------------------------
# Win condition
# ---------------------------------------------------------------------------

class TestWinCondition:
    def test_not_won_at_start(self):
        assert not make_game(level=1).is_level_complete()

    def test_win_level1(self):
        g = make_game(level=1, scroll=0.0)
        g.action()                      # pick up block 1
        g.scroll = peg_scroll(g, 2)
        g.action()                      # place on peg 2
        assert g.is_level_complete()

    def test_not_won_with_held_block(self):
        g = make_game(level=1, scroll=0.0)
        g.action()                      # block 1 now held
        g.pegs[2] = [1]                 # cheat: put it on peg2 anyway
        g.pegs[0] = []
        assert not g.is_level_complete()  # still held → not complete

    def test_not_won_until_all_blocks_on_peg2(self):
        g = make_game(level=2, scroll=0.0)
        # Move only block 1 to peg 2
        g.action()
        g.scroll = peg_scroll(g, 2)
        g.action()
        assert not g.is_level_complete()

    def test_win_level2_full_solve(self):
        g = make_game(level=2)
        # block1: peg0 → peg1
        g.scroll = peg_scroll(g, 0); g.action()
        g.scroll = peg_scroll(g, 1); g.action()
        # block2: peg0 → peg2
        g.scroll = peg_scroll(g, 0); g.action()
        g.scroll = peg_scroll(g, 2); g.action()
        # block1: peg1 → peg2
        g.scroll = peg_scroll(g, 1); g.action()
        g.scroll = peg_scroll(g, 2); g.action()
        assert g.is_level_complete()


# ---------------------------------------------------------------------------
# Level progression
# ---------------------------------------------------------------------------

class TestLevelProgression:
    def test_next_level_increments(self):
        g = make_game(level=1)
        g.next_level()
        assert g.level == 2

    def test_next_level_wraps_after_4(self):
        g = make_game(level=4)
        g.next_level()
        assert g.level == 1

    def test_level_cycle(self):
        g = GameState()
        for expected in [2, 3, 4, 1, 2, 3]:
            g.next_level()
            assert g.level == expected

    def test_next_level_resets_state_and_layout(self):
        g = make_game(level=1, scroll=0.0)
        g.action()                      # pick up
        g.scroll = peg_scroll(g, 2)
        g.action()                      # place → won
        g.next_level()
        assert g.level == 2
        assert g.pegs[0] == [2, 1]
        assert g.held_block is None
        assert g.scroll == 0.0
        assert g.peg_cols == compute_layout(2)[0]
        assert g.max_scroll == compute_layout(2)[2]


# ---------------------------------------------------------------------------
# Scroll update
# ---------------------------------------------------------------------------

class TestScrollUpdate:
    def test_tilt_left_scrolls_right(self):
        g = make_game(level=4, scroll=5.0)
        g.update_scroll(-512, 100)
        assert g.scroll > 5.0

    def test_tilt_right_scrolls_left(self):
        g = make_game(level=4, scroll=5.0)
        g.update_scroll(512, 100)
        assert g.scroll < 5.0

    def test_no_tilt_no_change(self):
        g = make_game(level=4, scroll=5.0)
        g.update_scroll(0, 100)
        assert g.scroll == 5.0

    def test_scroll_clamped_at_zero(self):
        g = make_game(level=4, scroll=0.0)
        g.update_scroll(1024, 100_000)
        assert g.scroll == 0.0

    def test_scroll_clamped_at_max(self):
        g = make_game(level=4)
        g.scroll = float(g.max_scroll)
        g.update_scroll(-1024, 100_000)
        assert g.scroll == float(g.max_scroll)

    def test_larger_tilt_moves_faster(self):
        g1 = make_game(level=4, scroll=5.0)
        g2 = make_game(level=4, scroll=5.0)
        g1.update_scroll(-256, 100)
        g2.update_scroll(-1024, 100)
        assert g2.scroll > g1.scroll

    def test_longer_dt_moves_more(self):
        g1 = make_game(level=4, scroll=5.0)
        g2 = make_game(level=4, scroll=5.0)
        g1.update_scroll(-512, 50)
        g2.update_scroll(-512, 200)
        assert g2.scroll > g1.scroll

    def test_scroll_int_truncates(self):
        g = make_game(scroll=3.9)
        assert g.scroll_int == 3

    def test_max_scroll_per_level(self):
        for level in range(1, 5):
            g = make_game(level=level)
            assert g.max_scroll == 4 * level


# ---------------------------------------------------------------------------
# Rendering – grid dimensions
# ---------------------------------------------------------------------------

class TestRenderDimensions:
    def test_returns_5_rows(self):
        assert len(render_frame(make_game())) == SCREEN_HEIGHT

    def test_each_row_has_5_cols(self):
        grid = render_frame(make_game())
        assert all(len(row) == SCREEN_WIDTH for row in grid)

    def test_all_values_in_range(self):
        g = make_game(level=4, scroll=5.0)
        g.action()   # pick up a block
        grid = render_frame(g, stick_on=True, held_on=True)
        for row in grid:
            for v in row:
                assert 0 <= v <= 9


# ---------------------------------------------------------------------------
# Rendering – sticks
# ---------------------------------------------------------------------------

class TestRenderSticks:
    def test_peg0_visible_at_scroll0(self):
        """Peg 0 is always at world col 2 = screen col 2 at scroll 0."""
        for level in range(1, 5):
            g = make_game(level=level)
            g.pegs = [[], [], []]
            g.scroll = 0.0
            grid = render_frame(g, stick_on=True, held_on=False)
            for row in range(PEG_ROW_TOP, SCREEN_HEIGHT):
                assert grid[row][2] >= BRIGHTNESS_STICK, \
                    f"level {level} row {row}" + grid_str(grid)

    def test_stick_hidden_when_off(self):
        g = make_game(level=1)
        g.pegs = [[], [], []]
        g.scroll = 0.0
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[2][2] == 0

    def test_peg1_visible_when_centred(self):
        for level in range(1, 5):
            g = make_game(level=level)
            g.pegs = [[], [], []]
            g.scroll = peg_scroll(g, 1)
            grid = render_frame(g, stick_on=True, held_on=False)
            for row in range(PEG_ROW_TOP, SCREEN_HEIGHT):
                assert grid[row][SCREEN_CENTER_COL] >= BRIGHTNESS_STICK, \
                    f"level {level}" + grid_str(grid)

    def test_peg2_visible_when_centred(self):
        for level in range(1, 5):
            g = make_game(level=level)
            g.pegs = [[], [], []]
            g.scroll = peg_scroll(g, 2)
            grid = render_frame(g, stick_on=True, held_on=False)
            for row in range(PEG_ROW_TOP, SCREEN_HEIGHT):
                assert grid[row][SCREEN_CENTER_COL] >= BRIGHTNESS_STICK, \
                    f"level {level}"

    def test_stick_not_drawn_in_row0(self):
        g = make_game(level=1)
        g.pegs = [[], [], []]
        g.scroll = 0.0
        grid = render_frame(g, stick_on=True, held_on=False)
        assert grid[HELD_ROW][2] == 0


# ---------------------------------------------------------------------------
# Rendering – placed blocks
# ---------------------------------------------------------------------------

class TestRenderBlocks:
    def test_block1_at_bottom_of_peg0(self):
        g = make_game(level=1, scroll=0.0)
        # peg0 at sc=2, block1 (width 1) at col 2
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[PEG_ROW_BOTTOM][2] == BRIGHTNESS_BLOCK, grid_str(grid)

    def test_block2_width3_centred_at_peg0(self):
        g = make_game(level=2, scroll=0.0)
        g.pegs = [[2], [], []]
        # peg0 at col 2; block2 half=1 → world cols 1-3 → sc 1-3
        grid = render_frame(g, stick_on=False, held_on=False)
        for sc in [1, 2, 3]:
            assert grid[PEG_ROW_BOTTOM][sc] == BRIGHTNESS_BLOCK, grid_str(grid)
        assert grid[PEG_ROW_BOTTOM][0] == 0
        assert grid[PEG_ROW_BOTTOM][4] == 0

    def test_block3_width5_fills_screen_at_peg0(self):
        g = make_game(level=3, scroll=0.0)
        g.pegs = [[3], [], []]
        # peg0 at col 2; block3 half=2 → world cols 0-4 → sc 0-4
        grid = render_frame(g, stick_on=False, held_on=False)
        for sc in range(5):
            assert grid[PEG_ROW_BOTTOM][sc] == BRIGHTNESS_BLOCK, grid_str(grid)

    def test_block1_stacked_above_block2(self):
        g = make_game(level=2, scroll=0.0)
        # depth 0 = block2 at row4, depth 1 = block1 at row3
        grid = render_frame(g, stick_on=False, held_on=False)
        for sc in [1, 2, 3]:
            assert grid[4][sc] == BRIGHTNESS_BLOCK
        assert grid[3][2] == BRIGHTNESS_BLOCK
        assert grid[3][1] == 0
        assert grid[3][3] == 0

    def test_block_overrides_stick(self):
        g = make_game(level=1, scroll=0.0)
        grid = render_frame(g, stick_on=True, held_on=False)
        # Block (9) beats stick (5) at same position
        assert grid[PEG_ROW_BOTTOM][2] == BRIGHTNESS_BLOCK

    def test_block_on_peg1_centred(self):
        for level in range(1, 5):
            g = make_game(level=level)
            g.pegs = [[], [1], []]
            g.scroll = peg_scroll(g, 1)
            grid = render_frame(g, stick_on=False, held_on=False)
            assert grid[PEG_ROW_BOTTOM][SCREEN_CENTER_COL] == BRIGHTNESS_BLOCK, \
                f"level {level}" + grid_str(grid)

    def test_scroll_shifts_block_on_screen(self):
        g = make_game(level=1, scroll=0.0)
        grid0 = render_frame(g, stick_on=False, held_on=False)
        g.scroll = 2.0          # peg0 now at sc=0
        grid2 = render_frame(g, stick_on=False, held_on=False)
        assert grid0[PEG_ROW_BOTTOM][2] == BRIGHTNESS_BLOCK
        assert grid2[PEG_ROW_BOTTOM][0] == BRIGHTNESS_BLOCK
        assert grid2[PEG_ROW_BOTTOM][2] == 0

    def test_four_blocks_stacked_rows(self):
        g = make_game(level=4, scroll=0.0)
        grid = render_frame(g, stick_on=False, held_on=False)
        # blocks 3,2,1 at rows 3,2,1 (block4 at row4 and wrapped)
        assert grid[3][2] == BRIGHTNESS_BLOCK   # block3 centre
        assert grid[2][2] == BRIGHTNESS_BLOCK   # block2 centre
        assert grid[1][2] == BRIGHTNESS_BLOCK   # block1 centre


# ---------------------------------------------------------------------------
# Rendering – 7-wide block overflow wrap
# ---------------------------------------------------------------------------

class TestBlock4Wrap:
    def _game_with_block4_on_peg0(self):
        g = make_game(level=4, scroll=0.0)
        g.pegs = [[4], [], []]
        return g

    def test_main_row_fully_lit(self):
        """At scroll 0 peg0 is at sc=2; block4 spans sc -1..5; cols 0-4 lit."""
        grid = render_frame(self._game_with_block4_on_peg0(),
                            stick_on=False, held_on=False)
        for sc in range(5):
            assert grid[4][sc] == BRIGHTNESS_BLOCK, \
                f"col {sc} not lit" + grid_str(grid)

    def test_left_overflow_wraps_to_row_above(self):
        """sc = -1 → wrapped to (row-1, col 4)."""
        grid = render_frame(self._game_with_block4_on_peg0(),
                            stick_on=False, held_on=False)
        assert grid[3][4] == BRIGHTNESS_BLOCK, grid_str(grid)

    def test_right_overflow_wraps_to_row_above(self):
        """sc = 5 → wrapped to (row-1, col 0)."""
        grid = render_frame(self._game_with_block4_on_peg0(),
                            stick_on=False, held_on=False)
        assert grid[3][0] == BRIGHTNESS_BLOCK, grid_str(grid)

    def test_no_wrap_for_blocks_1_to_3(self):
        """Blocks 1-3 centred at peg0 should never produce wrap pixels."""
        for block_num in [1, 2, 3]:
            g = make_game(level=block_num, scroll=0.0)
            g.pegs = [[block_num], [], []]
            grid = render_frame(g, stick_on=False, held_on=False)
            assert all(v == 0 for v in grid[3]), \
                f"Unexpected pixel in row 3 for block {block_num}" + grid_str(grid)

    def test_block4_wraps_on_peg1_centred(self):
        g = make_game(level=4)
        g.pegs = [[], [4], []]
        g.scroll = peg_scroll(g, 1)    # peg1 at sc=2
        grid = render_frame(g, stick_on=False, held_on=False)
        for sc in range(5):
            assert grid[4][sc] == BRIGHTNESS_BLOCK
        assert grid[3][4] == BRIGHTNESS_BLOCK
        assert grid[3][0] == BRIGHTNESS_BLOCK

    def test_block4_held_wraps_to_bottom_row(self):
        """Held block 4 at row 0 has no row above; overflow wraps to row 4."""
        g = make_game(level=4)
        g.pegs = [[], [], []]
        g.held_block = 4
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        # Top row: centre 5 pixels lit
        for sc in range(SCREEN_WIDTH):
            assert grid[HELD_ROW][sc] == BRIGHTNESS_HELD
        # Bottom row: two wrap corners lit
        assert grid[SCREEN_HEIGHT - 1][0] == BRIGHTNESS_HELD,  "right overflow → (4,0)"
        assert grid[SCREEN_HEIGHT - 1][SCREEN_WIDTH - 1] == BRIGHTNESS_HELD, "left overflow → (4,4)"


# ---------------------------------------------------------------------------
# Rendering – held block
# ---------------------------------------------------------------------------

class TestRenderHeld:
    def test_held_block1_at_top_centre(self):
        g = make_game(level=1)
        g.held_block = 1
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        assert grid[HELD_ROW][SCREEN_CENTER_COL] == BRIGHTNESS_HELD

    def test_held_block2_spans_3_cols(self):
        g = make_game(level=1)
        g.held_block = 2
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        for sc in [1, 2, 3]:
            assert grid[HELD_ROW][sc] == BRIGHTNESS_HELD
        assert grid[HELD_ROW][0] == 0
        assert grid[HELD_ROW][4] == 0

    def test_held_block_hidden_when_off(self):
        g = make_game(level=1)
        g.held_block = 2
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for v in grid[HELD_ROW])

    def test_held_block_independent_of_scroll(self):
        for level in range(1, 5):
            g = make_game(level=level)
            g.held_block = 1
            g.held_from_peg = 0
            for scroll in [0.0, peg_scroll(g, 1), float(g.max_scroll)]:
                g.scroll = scroll
                grid = render_frame(g, stick_on=False, held_on=True)
                assert grid[HELD_ROW][SCREEN_CENTER_COL] == BRIGHTNESS_HELD, \
                    f"level {level} scroll {scroll}" + grid_str(grid)

    def test_held_block3_fills_top_row(self):
        g = make_game(level=1)
        g.held_block = 3
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        for sc in range(5):
            assert grid[HELD_ROW][sc] == BRIGHTNESS_HELD

    def test_held_block4_wraps_to_bottom_row(self):
        """7-wide held block at row 0: centre 5 lit, overflow corners wrap to row 4."""
        g = make_game(level=4)
        g.pegs = [[], [], []]   # no placed blocks so wrap pixels are unobstructed
        g.held_block = 4
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        # Centre 5 pixels on top row
        for sc in range(SCREEN_WIDTH):
            assert grid[HELD_ROW][sc] == BRIGHTNESS_HELD
        # Two overflow corners on bottom row (the 'bend' for the held block)
        assert grid[SCREEN_HEIGHT - 1][SCREEN_WIDTH - 1] == BRIGHTNESS_HELD
        assert grid[SCREEN_HEIGHT - 1][0] == BRIGHTNESS_HELD

    def test_no_held_block_row0_empty(self):
        g = make_game(level=1, scroll=0.0)
        grid = render_frame(g, stick_on=False, held_on=True)
        assert grid[HELD_ROW][SCREEN_CENTER_COL] == 0   # block on peg, not held


# ---------------------------------------------------------------------------
# Integration – full level solves
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_level1_solve(self):
        g = GameState()
        assert not g.is_level_complete()

        g.scroll = peg_scroll(g, 0); g.action()     # pick up
        g.scroll = peg_scroll(g, 2); g.action()     # place on peg2

        assert g.is_level_complete()
        g.next_level()
        assert g.level == 2
        assert g.pegs[0] == [2, 1]

    def test_level2_minimum_solve(self):
        g = make_game(level=2)
        moves = [
            (0, 1),    # block 1: peg0 → peg1
            (0, 2),    # block 2: peg0 → peg2
            (1, 2),    # block 1: peg1 → peg2
        ]
        for src, dst in moves:
            g.scroll = peg_scroll(g, src); assert g.action() is True
            g.scroll = peg_scroll(g, dst); assert g.action() is True
        assert g.is_level_complete()

    def test_render_after_pickup_shows_held(self):
        g = make_game(level=1, scroll=0.0)
        g.action()
        grid = render_frame(g, stick_on=False, held_on=True)
        assert grid[HELD_ROW][SCREEN_CENTER_COL] == BRIGHTNESS_HELD
        assert grid[PEG_ROW_BOTTOM][SCREEN_CENTER_COL] == 0

    def test_cancel_restores_render(self):
        g = make_game(level=1, scroll=0.0)
        g.action()
        g.cancel()
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[PEG_ROW_BOTTOM][SCREEN_CENTER_COL] == BRIGHTNESS_BLOCK
        assert all(v == 0 for v in grid[HELD_ROW])

    def test_all_levels_complete_and_cycle(self):
        """Solve each level in minimum moves and verify cycling."""
        g = GameState()
        for level in range(1, 5):
            assert g.level == level
            _solve_hanoi(g, level, 0, 2, 1)
            assert g.is_level_complete(), f"level {level} not complete"
            g.next_level()
        assert g.level == 1   # cycled back


# ---------------------------------------------------------------------------
# Regression tests – wrap artefact bug
# ---------------------------------------------------------------------------

class TestNoWrapArtifacts:
    """
    Regression suite for the ghost-pixel artefact introduced when the wrap
    logic applied to *any* off-screen pixel rather than only the single
    overflow pixel of the 7-wide block.

    Root cause: _draw_world_block was mapping sc < 0 → sc+5 for every block,
    so a block at sc=-2 silently appeared at sc=3 in the row above.  The fix
    restricts wrapping to block 4 only, and only for sc==-1 or sc==SCREEN_WIDTH
    (exactly one step out of bounds on either edge).
    """

    # ── exact scenarios reported by the user ─────────────────────────────

    def test_level1_scroll_right_no_ghost(self):
        """Level 1 bug report: scrolling right before pickup shows a single
        bright dot to the right of peg 2, one row up."""
        g = make_game(level=1)          # block1 on peg0, world col 2
        g.scroll = float(g.max_scroll)  # scroll=4 → block sc=-2
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for row in grid for v in row), \
            "Ghost pixel when block1 scrolled off-screen" + grid_str(grid)

    def test_level2_ghost_on_second_tower(self):
        """Level 2 bug report: ghost two-block overlay on peg1 one row up
        (blocks at peg0 and peg1 wrapping into row 3 when viewing peg2)."""
        g = make_game(level=2)
        g.pegs = [[2], [1], []]         # mid-solve state
        g.scroll = 7.0                  # scroll_int=7: block2 centre sc=-5,
                                        # block1 centre sc=-1 → both wrap spuriously
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for row in grid for v in row), \
            "Ghost pixels visible when blocks scrolled off-screen" + grid_str(grid)

    # ── blocks 1-3 must never produce wrap pixels ─────────────────────────

    def test_block1_no_wrap_at_sc_minus1(self):
        """block1 at sc=-1 (scroll=3, level 1) must not wrap to row above."""
        g = make_game(level=1)
        g.scroll = 3.0    # block1 at world col 2 → sc = 2-3 = -1
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for row in grid for v in row), grid_str(grid)

    def test_block1_no_wrap_at_sc_minus2(self):
        g = make_game(level=1)
        g.scroll = 4.0    # sc = 2-4 = -2
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for row in grid for v in row), grid_str(grid)

    def test_block2_right_edge_no_wrap(self):
        """block2 right edge (dc=+1) at sc=-1 must not wrap."""
        g = make_game(level=2)
        g.pegs = [[2], [], []]
        g.scroll = 4.0    # peg0 col 2: dc=+1 → sc = 3-4 = -1
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for row in grid for v in row), grid_str(grid)

    def test_block3_no_wrap_when_off_screen(self):
        g = make_game(level=3)
        g.pegs = [[3], [], []]
        g.scroll = peg_scroll(g, 2)   # block far off to the left
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for row in grid for v in row), grid_str(grid)

    def test_no_wrap_for_any_block_at_every_scroll(self):
        """Exhaustive: blocks 1-3 never produce pixels when the block is
        entirely off-screen (i.e. no pixel of the block falls in sc 0-4)."""
        for level in range(1, 4):
            g = make_game(level=level)
            g.pegs = [[level], [], []]  # single widest block on peg 0
            half = BLOCK_WIDTHS[level] // 2
            # Sample every integer scroll from 0 to max_scroll
            for s in range(g.max_scroll + 1):
                g.scroll = float(s)
                peg_sc = g.peg_cols[0] - s          # screen col of block centre
                # Skip if any pixel of the block is legitimately on-screen
                if peg_sc + half >= 0 and peg_sc - half < SCREEN_WIDTH:
                    continue
                grid = render_frame(g, stick_on=False, held_on=False)
                assert all(v == 0 for row in grid for v in row), \
                    f"level {level} scroll {s}: ghost pixel" + grid_str(grid)

    # ── block 4 wrap must still work correctly ────────────────────────────

    def test_block4_wraps_when_centred_peg0(self):
        g = make_game(level=4)
        g.pegs = [[4], [], []]
        g.scroll = 0.0    # peg0 at sc=2; block spans sc -1..5
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[3][4] == BRIGHTNESS_BLOCK, "Left overflow must wrap to (3,4)"
        assert grid[3][0] == BRIGHTNESS_BLOCK, "Right overflow must wrap to (3,0)"

    def test_block4_no_ghost_when_far_off_screen(self):
        """Block 4 scrolled many steps away must not produce spurious wrap pixels."""
        g = make_game(level=4)
        g.pegs = [[4], [], []]
        g.scroll = 8.0    # peg0 at sc=2-8=-6; block spans sc -9..-3 → no sc==-1
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for row in grid for v in row), \
            "Block 4 far off-screen produced ghost pixels" + grid_str(grid)

    def test_block4_wrap_only_when_exactly_centred(self):
        """Block 4 wrap appears only when the peg is exactly at screen centre;
        one scroll step off-centre must produce no wrap pixels (no sticky artefact)."""
        g = make_game(level=4)
        g.pegs = [[4], [], []]

        # scroll=0: peg0 world col 2, screen col 2 (centred) → both wraps show
        g.scroll = 0.0
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[3][4] == BRIGHTNESS_BLOCK, "left wrap at centred scroll"
        assert grid[3][0] == BRIGHTNESS_BLOCK, "right wrap at centred scroll"

        # scroll=1: peg0 at screen col 1 (not centred) → no wrap at all
        g.scroll = 1.0
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[3][4] == 0, "no wrap one step right of centre"
        assert grid[3][0] == 0, "no wrap one step right of centre"

    def test_block4_sticky_wrap_regression(self):
        """Regression for the sticky-wrap bug: the wrap pixel at (row3,col4)
        must disappear as soon as the player scrolls away from the centred position,
        not persist for 6 scroll steps as each right-side pixel of the 7-wide block
        passes through sc==-1."""
        g = make_game(level=4)
        g.pegs = [[4], [], []]
        # Confirmed-bad scrolls from the original bug (scrolls 1-6 all showed
        # ghost pixel at row3 col4 before the fix)
        for s in range(1, 7):
            g.scroll = float(s)
            grid = render_frame(g, stick_on=False, held_on=False)
            assert grid[3][4] == 0, \
                f"Sticky wrap pixel at (3,4) for scroll={s}" + grid_str(grid)
            assert grid[3][0] == 0, \
                f"Sticky wrap pixel at (3,0) for scroll={s}" + grid_str(grid)

    def test_held_block4_bend_around_regression(self):
        """Regression: held block 4 showed flat 5 dots with no indication of its
        7-pixel width.  After the fix the two overflow pixels wrap to the bottom row,
        mirroring the bend-around behaviour of a placed block 4."""
        g = make_game(level=4)
        g.pegs = [[], [], []]
        g.held_block = 4
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        # Top row: all 5 lit (centre 5 of the 7-wide block)
        assert all(grid[HELD_ROW][sc] == BRIGHTNESS_HELD for sc in range(SCREEN_WIDTH))
        # Bottom-row corners: the two overflow pixels that bend around
        assert grid[SCREEN_HEIGHT - 1][0] == BRIGHTNESS_HELD, \
            "right overflow must wrap to bottom-left corner"
        assert grid[SCREEN_HEIGHT - 1][SCREEN_WIDTH - 1] == BRIGHTNESS_HELD, \
            "left overflow must wrap to bottom-right corner"


def _solve_hanoi(game, n, src, dst, aux):
    """Recursive Tower of Hanoi solver using the game's action() interface."""
    if n == 0:
        return
    _solve_hanoi(game, n - 1, src, aux, dst)
    game.scroll = peg_scroll(game, src)
    assert game.action() is True, f"pick up from peg {src} failed"
    game.scroll = peg_scroll(game, dst)
    assert game.action() is True, f"place on peg {dst} failed"
    _solve_hanoi(game, n - 1, aux, dst, src)
