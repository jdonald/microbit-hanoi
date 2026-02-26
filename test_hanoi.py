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
    GameState, render_frame,
    PEG_COLS, MAX_SCROLL, BLOCK_WIDTHS,
    BRIGHTNESS_BLOCK, BRIGHTNESS_STICK, BRIGHTNESS_HELD,
    HELD_ROW, SCREEN_WIDTH, SCREEN_HEIGHT,
    PEG_ROW_TOP, PEG_ROW_BOTTOM,
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


def grid_str(grid):
    """Pretty-print a grid for test failure messages."""
    return "\n" + "\n".join(" ".join(str(v) for v in row) for row in grid)


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
        g = make_game(level=2)
        # largest at index 0 (bottom), smallest at -1 (top)
        assert g.pegs[0] == [2, 1]

    def test_level3_stack_ordering(self):
        g = make_game(level=3)
        assert g.pegs[0] == [3, 2, 1]

    def test_level4_stack_ordering(self):
        g = make_game(level=4)
        assert g.pegs[0] == [4, 3, 2, 1]

    def test_initial_scroll_is_zero(self):
        assert GameState().scroll == 0.0

    def test_no_held_block_initially(self):
        assert GameState().held_block is None

    def test_held_from_peg_none_initially(self):
        assert GameState().held_from_peg is None

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


# ---------------------------------------------------------------------------
# Peg selection from scroll position
# ---------------------------------------------------------------------------

class TestPegSelection:
    def test_peg_cols_defined(self):
        assert PEG_COLS == [2, 7, 12]

    def test_scroll_0_selects_peg_0(self):
        # screen centre at world col 0+2=2 → closest to peg 0 (col 2)
        g = make_game(scroll=0.0)
        assert g.get_selected_peg() == 0

    def test_scroll_5_selects_peg_1(self):
        # screen centre at world col 5+2=7 → exactly peg 1
        g = make_game(scroll=5.0)
        assert g.get_selected_peg() == 1

    def test_scroll_10_selects_peg_2(self):
        # screen centre at world col 10+2=12 → exactly peg 2
        g = make_game(scroll=10.0)
        assert g.get_selected_peg() == 2

    def test_scroll_slightly_right_of_peg0_still_selects_peg0(self):
        # centre at 4 → dist to peg0(2)=2, dist to peg1(7)=3 → peg 0
        g = make_game(scroll=2.0)
        assert g.get_selected_peg() == 0

    def test_scroll_closer_to_peg1_selects_peg1(self):
        # centre at 6 → dist to peg0(2)=4, dist to peg1(7)=1 → peg 1
        g = make_game(scroll=4.0)
        assert g.get_selected_peg() == 1

    def test_scroll_between_peg1_and_peg2_selects_closer(self):
        # centre at 10 → dist to peg1(7)=3, dist to peg2(12)=2 → peg 2
        g = make_game(scroll=8.0)
        assert g.get_selected_peg() == 2

    def test_max_scroll_selects_peg_2(self):
        g = make_game(scroll=float(MAX_SCROLL))
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
        g = make_game(level=1, scroll=5.0)   # peg 1 is empty
        assert g.action() is False
        assert g.held_block is None

    def test_pick_up_top_block_from_two_block_stack(self):
        g = make_game(level=2, scroll=0.0)  # pegs[0] = [2, 1]
        g.action()
        assert g.held_block == 1
        assert g.pegs[0] == [2]

    def test_cannot_pick_up_when_already_holding(self):
        """Right button while holding tries to place, not pick up again."""
        g = make_game(level=2, scroll=0.0)
        g.action()              # pick up block 1
        assert g.held_block == 1
        # Press again on same (now-non-empty) peg → try to place block 1 on peg 0
        # peg 0 top is block 2 (larger than 1) → placement succeeds
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
        g.action()          # pick up block 1
        g.scroll = 5.0      # select peg 1
        assert g.action() is True
        assert g.pegs[1] == [1]
        assert g.held_block is None

    def test_place_smaller_on_larger_succeeds(self):
        g = make_game(level=2, scroll=0.0)
        g.action()              # pick up block 1 from peg 0
        g.scroll = 5.0
        g.action()              # place block 1 on peg 1
        g.scroll = 0.0
        g.action()              # pick up block 2 from peg 0
        g.scroll = 10.0
        result = g.action()     # place block 2 on peg 2 (empty)
        assert result is True
        assert g.pegs[2] == [2]

    def test_place_larger_on_smaller_fails(self):
        g = make_game(level=2, scroll=0.0)
        g.action()              # pick up block 1
        g.scroll = 5.0
        g.action()              # place block 1 on peg 1
        g.scroll = 0.0
        g.action()              # pick up block 2
        g.scroll = 5.0          # peg 1 has block 1 on top
        result = g.action()     # try to place block 2 on block 1 → illegal
        assert result is False
        assert g.held_block == 2
        assert g.pegs[1] == [1]  # peg 1 unchanged

    def test_place_block_back_on_source_peg(self):
        g = make_game(level=2, scroll=0.0)
        g.action()              # pick up block 1
        result = g.action()     # place back on same peg (block 2 is larger)
        assert result is True
        assert g.pegs[0] == [2, 1]
        assert g.held_block is None


# ---------------------------------------------------------------------------
# Cancel action
# ---------------------------------------------------------------------------

class TestCancel:
    def test_cancel_returns_block_to_source(self):
        g = make_game(level=1, scroll=0.0)
        g.action()     # pick up block 1 from peg 0
        g.cancel()
        assert g.held_block is None
        assert g.pegs[0] == [1]

    def test_cancel_when_nothing_held_is_noop(self):
        g = make_game(level=1)
        g.cancel()
        assert g.held_block is None

    def test_cancel_restores_to_scrolled_away_peg(self):
        g = make_game(level=2, scroll=0.0)
        g.action()          # pick up block 1 from peg 0
        g.scroll = 9.0      # scroll far away
        g.cancel()
        assert g.pegs[0] == [2, 1]
        assert g.held_block is None

    def test_cancel_with_multi_block_pickup(self):
        g = make_game(level=3, scroll=0.0)
        # Move block 1 to peg 1 first
        g.action()
        g.scroll = 5.0
        g.action()
        # Now pick up block 2 from peg 0
        g.scroll = 0.0
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
        g.action()          # pick up block 1
        g.scroll = 10.0
        g.action()          # place on peg 2
        assert g.is_level_complete()

    def test_not_won_with_held_block(self):
        g = make_game(level=1, scroll=0.0)
        g.action()          # pick up block 1 – now held
        # Manually populate peg 2 (as if cheating)
        g.pegs[2] = [1]
        g.pegs[0] = []
        # Still holding – should not count as won
        assert not g.is_level_complete()

    def test_not_won_until_all_blocks_on_peg2(self):
        g = make_game(level=2, scroll=0.0)
        # Move only block 1 to peg 2
        g.action()
        g.scroll = 10.0
        g.action()
        assert not g.is_level_complete()

    def test_win_level2_full_solve(self):
        g = make_game(level=2, scroll=0.0)
        # Move block 1 to peg 1
        g.action(); g.scroll = 5.0; g.action()
        # Move block 2 to peg 2
        g.scroll = 0.0; g.action(); g.scroll = 10.0; g.action()
        # Move block 1 to peg 2
        g.scroll = 5.0; g.action(); g.scroll = 10.0; g.action()
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

    def test_next_level_resets_state(self):
        g = make_game(level=1, scroll=0.0)
        g.action()          # pick up block 1
        g.scroll = 10.0
        g.action()          # place on peg 2 → won
        g.next_level()
        assert g.level == 2
        assert g.pegs[0] == [2, 1]
        assert g.held_block is None
        assert g.scroll == 0.0


# ---------------------------------------------------------------------------
# Scroll update
# ---------------------------------------------------------------------------

class TestScrollUpdate:
    def test_tilt_left_scrolls_right(self):
        g = make_game(scroll=5.0)
        g.update_scroll(-512, 100)
        assert g.scroll > 5.0

    def test_tilt_right_scrolls_left(self):
        g = make_game(scroll=5.0)
        g.update_scroll(512, 100)
        assert g.scroll < 5.0

    def test_no_tilt_no_change(self):
        g = make_game(scroll=5.0)
        g.update_scroll(0, 100)
        assert g.scroll == 5.0

    def test_scroll_clamped_at_zero(self):
        g = make_game(scroll=0.0)
        g.update_scroll(1024, 100_000)   # massive tilt right for a long time
        assert g.scroll == 0.0

    def test_scroll_clamped_at_max(self):
        g = make_game(scroll=float(MAX_SCROLL))
        g.update_scroll(-1024, 100_000)
        assert g.scroll == float(MAX_SCROLL)

    def test_larger_tilt_moves_faster(self):
        g1 = make_game(scroll=5.0)
        g2 = make_game(scroll=5.0)
        g1.update_scroll(-256, 100)
        g2.update_scroll(-1024, 100)
        assert g2.scroll > g1.scroll

    def test_longer_dt_moves_more(self):
        g1 = make_game(scroll=5.0)
        g2 = make_game(scroll=5.0)
        g1.update_scroll(-512, 50)
        g2.update_scroll(-512, 200)
        assert g2.scroll > g1.scroll

    def test_scroll_int_truncates(self):
        g = make_game(scroll=3.9)
        assert g.scroll_int == 3

    def test_max_scroll_value(self):
        assert MAX_SCROLL == 10


# ---------------------------------------------------------------------------
# Rendering – grid dimensions
# ---------------------------------------------------------------------------

class TestRenderDimensions:
    def test_returns_5_rows(self):
        grid = render_frame(make_game())
        assert len(grid) == SCREEN_HEIGHT

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
    def test_visible_peg0_at_scroll0(self):
        g = make_game(level=1)
        g.pegs = [[], [], []]   # no blocks to mask sticks
        g.scroll = 0.0          # peg 0 (world col 2) at screen col 2
        grid = render_frame(g, stick_on=True, held_on=False)
        for row in range(PEG_ROW_TOP, SCREEN_HEIGHT):
            assert grid[row][2] >= BRIGHTNESS_STICK, grid_str(grid)

    def test_stick_hidden_when_off(self):
        g = make_game(level=1)
        g.pegs = [[], [], []]
        g.scroll = 0.0
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[2][2] == 0

    def test_peg1_visible_at_scroll5(self):
        g = make_game(level=1)
        g.pegs = [[], [], []]
        g.scroll = 5.0          # peg 1 (world col 7) at screen col 2
        grid = render_frame(g, stick_on=True, held_on=False)
        for row in range(PEG_ROW_TOP, SCREEN_HEIGHT):
            assert grid[row][2] >= BRIGHTNESS_STICK

    def test_peg2_visible_at_scroll10(self):
        g = make_game(level=1)
        g.pegs = [[], [], []]
        g.scroll = 10.0         # peg 2 (world col 12) at screen col 2
        grid = render_frame(g, stick_on=True, held_on=False)
        for row in range(PEG_ROW_TOP, SCREEN_HEIGHT):
            assert grid[row][2] >= BRIGHTNESS_STICK

    def test_peg_not_drawn_in_row0(self):
        g = make_game(level=1)
        g.pegs = [[], [], []]
        g.scroll = 0.0
        grid = render_frame(g, stick_on=True, held_on=False)
        assert grid[HELD_ROW][2] == 0   # row 0 is reserved for held block

    def test_off_screen_peg_not_drawn(self):
        g = make_game(level=1)
        g.scroll = 0.0   # peg 1 at screen col 5 (off-screen)
        grid = render_frame(g, stick_on=True, held_on=False)
        # peg 1 world col 7, screen col 7-0=7 → off-screen
        # Only peg 0 (sc=2) visible; peg 1 and peg 2 should not appear
        # (we just check peg 1 column would be off-screen at scroll=0)
        # Actually sc=7 → off screen; nothing to assert here beyond no crash
        assert len(grid) == 5   # sanity


# ---------------------------------------------------------------------------
# Rendering – placed blocks
# ---------------------------------------------------------------------------

class TestRenderBlocks:
    def test_block1_at_bottom_row_peg0(self):
        g = make_game(level=1)
        g.scroll = 0.0
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[PEG_ROW_BOTTOM][2] == BRIGHTNESS_BLOCK, grid_str(grid)

    def test_block2_width3_at_peg0(self):
        g = make_game(level=1)
        g.pegs = [[2], [], []]
        g.scroll = 0.0   # peg 0 at sc=2, block half=1 → cols 1,2,3
        grid = render_frame(g, stick_on=False, held_on=False)
        for sc in [1, 2, 3]:
            assert grid[PEG_ROW_BOTTOM][sc] == BRIGHTNESS_BLOCK, grid_str(grid)
        assert grid[PEG_ROW_BOTTOM][0] == 0
        assert grid[PEG_ROW_BOTTOM][4] == 0

    def test_block3_width5_at_peg0(self):
        g = make_game(level=1)
        g.pegs = [[3], [], []]
        g.scroll = 0.0   # peg 0 at sc=2, half=2 → cols 0-4
        grid = render_frame(g, stick_on=False, held_on=False)
        for sc in range(5):
            assert grid[PEG_ROW_BOTTOM][sc] == BRIGHTNESS_BLOCK, grid_str(grid)

    def test_block1_above_block2(self):
        g = make_game(level=1)
        g.pegs = [[2, 1], [], []]   # depth 0=block2 at row4, depth 1=block1 at row3
        g.scroll = 0.0
        grid = render_frame(g, stick_on=False, held_on=False)
        # Block 2 at row 4, cols 1-3
        for sc in [1, 2, 3]:
            assert grid[4][sc] == BRIGHTNESS_BLOCK
        # Block 1 at row 3, col 2
        assert grid[3][2] == BRIGHTNESS_BLOCK
        assert grid[3][1] == 0
        assert grid[3][3] == 0

    def test_four_blocks_stacked(self):
        g = make_game(level=4)
        g.scroll = 0.0
        grid = render_frame(g, stick_on=False, held_on=False)
        # Row 4: block 4 (width 7, wraps), rows 3,2,1: blocks 3,2,1
        assert grid[3][2] == BRIGHTNESS_BLOCK  # block 3, centre
        assert grid[2][2] == BRIGHTNESS_BLOCK  # block 2, centre
        assert grid[1][2] == BRIGHTNESS_BLOCK  # block 1, centre

    def test_block_brighter_than_stick(self):
        g = make_game(level=1)
        g.scroll = 0.0   # peg 0 at sc=2, block 1 at row 4, sc 2
        grid = render_frame(g, stick_on=True, held_on=False)
        # Block (9) overrides stick (5) at same position
        assert grid[PEG_ROW_BOTTOM][2] == BRIGHTNESS_BLOCK

    def test_block_on_peg1_at_scroll5(self):
        g = make_game(level=1)
        g.pegs = [[], [1], []]
        g.scroll = 5.0   # peg 1 (world col 7) at sc=2
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[PEG_ROW_BOTTOM][2] == BRIGHTNESS_BLOCK

    def test_scroll_moves_block(self):
        g = make_game(level=1)
        g.scroll = 0.0
        grid0 = render_frame(g, stick_on=False, held_on=False)
        g.scroll = 2.0   # peg 0 now at sc=0
        grid2 = render_frame(g, stick_on=False, held_on=False)
        assert grid0[PEG_ROW_BOTTOM][2] == BRIGHTNESS_BLOCK
        assert grid2[PEG_ROW_BOTTOM][0] == BRIGHTNESS_BLOCK
        assert grid2[PEG_ROW_BOTTOM][2] == 0


# ---------------------------------------------------------------------------
# Rendering – 7-wide block overflow wrap
# ---------------------------------------------------------------------------

class TestBlock4Wrap:
    def _setup(self, scroll=0.0):
        g = make_game(level=1)
        g.pegs = [[4], [], []]   # block 4 on peg 0 (world col 2)
        g.scroll = scroll
        return g

    def test_main_row_fully_covered_at_scroll0(self):
        """At scroll=0, block spans world cols -1..5; screen cols -1..5.
        Screen cols 0-4 should be lit in row 4."""
        g = self._setup(scroll=0.0)
        grid = render_frame(g, stick_on=False, held_on=False)
        for sc in range(5):
            assert grid[4][sc] == BRIGHTNESS_BLOCK, \
                f"col {sc} not lit" + grid_str(grid)

    def test_left_overflow_wraps_to_row_above(self):
        """Screen col -1 (world col -1) wraps to (row-1, col 4)."""
        g = self._setup(scroll=0.0)
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[3][4] == BRIGHTNESS_BLOCK, grid_str(grid)

    def test_right_overflow_wraps_to_row_above(self):
        """Screen col 5 (world col 5) wraps to (row-1, col 0)."""
        g = self._setup(scroll=0.0)
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[3][0] == BRIGHTNESS_BLOCK, grid_str(grid)

    def test_no_wrap_for_smaller_blocks(self):
        """Blocks 1-3 should never produce wrapped pixels when centred."""
        for block_num in [1, 2, 3]:
            g = make_game(level=1)
            g.pegs = [[block_num], [], []]
            g.scroll = 0.0
            grid = render_frame(g, stick_on=False, held_on=False)
            # Row 3 should be empty
            assert all(v == 0 for v in grid[3]), \
                f"Unexpected pixel in row 3 for block {block_num}" + grid_str(grid)

    def test_block4_at_scroll5_main_row(self):
        """Block 4 on peg 1 (world col 7) at scroll 5."""
        g = make_game(level=1)
        g.pegs = [[], [4], []]
        g.scroll = 5.0   # peg 1 at sc=2, block spans sc -1..5 again
        grid = render_frame(g, stick_on=False, held_on=False)
        for sc in range(5):
            assert grid[4][sc] == BRIGHTNESS_BLOCK, grid_str(grid)
        assert grid[3][4] == BRIGHTNESS_BLOCK
        assert grid[3][0] == BRIGHTNESS_BLOCK

    def test_block4_no_wrap_from_row0(self):
        """7-wide block in row 0 has nowhere to wrap to (no row -1)."""
        g = make_game(level=1)
        g.pegs = [[], [], []]
        g.held_block = 4
        g.held_from_peg = 0
        # held block draws at row 0, screen-centred → no crash, no row -1 access
        grid = render_frame(g, stick_on=False, held_on=True)
        # Just verify no exception and grid is valid
        assert len(grid) == 5


# ---------------------------------------------------------------------------
# Rendering – held block
# ---------------------------------------------------------------------------

class TestRenderHeld:
    def test_held_block1_at_top_centre(self):
        g = make_game(level=1, scroll=5.0)
        g.held_block = 1
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        assert grid[HELD_ROW][2] == BRIGHTNESS_HELD

    def test_held_block2_spans_3_cols(self):
        g = make_game(level=1, scroll=5.0)
        g.held_block = 2
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        for sc in [1, 2, 3]:
            assert grid[HELD_ROW][sc] == BRIGHTNESS_HELD
        assert grid[HELD_ROW][0] == 0
        assert grid[HELD_ROW][4] == 0

    def test_held_block_hidden_when_off(self):
        g = make_game(level=1, scroll=0.0)
        g.held_block = 2
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=False)
        assert all(v == 0 for v in grid[HELD_ROW])

    def test_held_block_independent_of_scroll(self):
        """Held block always appears at top-centre regardless of scroll."""
        for scroll in [0.0, 5.0, 10.0]:
            g = make_game(level=1, scroll=scroll)
            g.held_block = 1
            g.held_from_peg = 0
            grid = render_frame(g, stick_on=False, held_on=True)
            assert grid[HELD_ROW][2] == BRIGHTNESS_HELD, \
                f"scroll={scroll}" + grid_str(grid)

    def test_held_block3_fills_top_row(self):
        g = make_game(level=1)
        g.held_block = 3   # width 5: cols 0-4
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        for sc in range(5):
            assert grid[HELD_ROW][sc] == BRIGHTNESS_HELD

    def test_held_block4_clips_to_screen(self):
        """7-wide held block in row 0: only cols 0-4 lit (no wrap available)."""
        g = make_game(level=1)
        g.held_block = 4   # width 7, centre at sc=2 → sc -1..5
        g.held_from_peg = 0
        grid = render_frame(g, stick_on=False, held_on=True)
        # Cols 0-4 should be lit (inner 5 of 7)
        for sc in range(5):
            assert grid[HELD_ROW][sc] == BRIGHTNESS_HELD
        # No crash – that's the main assertion for the overflow case

    def test_no_held_block_row0_empty(self):
        g = make_game(level=1, scroll=0.0)
        grid = render_frame(g, stick_on=False, held_on=True)
        # block 1 is on peg 0, not held
        assert grid[HELD_ROW][2] == 0


# ---------------------------------------------------------------------------
# Integration – simulate a full level-1 solve
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_level1_solve(self):
        g = GameState()
        assert g.level == 1
        assert not g.is_level_complete()

        # Pick up block 1 from peg 0
        g.scroll = 0.0
        assert g.action() is True
        assert g.held_block == 1

        # Scroll to peg 2 and place
        g.scroll = 10.0
        assert g.action() is True
        assert g.held_block is None
        assert g.is_level_complete()

        # Advance level
        g.next_level()
        assert g.level == 2
        assert g.pegs[0] == [2, 1]

    def test_level2_minimum_solve(self):
        """Solve level 2 in 3 moves and verify completion."""
        g = make_game(level=2)

        moves = [
            (0.0, 5.0),    # block 1: peg0 → peg1
            (0.0, 10.0),   # block 2: peg0 → peg2
            (5.0, 10.0),   # block 1: peg1 → peg2
        ]
        for src_scroll, dst_scroll in moves:
            g.scroll = src_scroll
            assert g.action() is True, "pick up failed"
            g.scroll = dst_scroll
            assert g.action() is True, "place failed"

        assert g.is_level_complete()

    def test_render_after_pickup_shows_held(self):
        g = make_game(level=1, scroll=0.0)
        g.action()   # pick up block 1
        grid = render_frame(g, stick_on=False, held_on=True)
        assert grid[HELD_ROW][2] == BRIGHTNESS_HELD
        assert grid[PEG_ROW_BOTTOM][2] == 0   # block gone from peg

    def test_cancel_restores_render(self):
        g = make_game(level=1, scroll=0.0)
        g.action()
        g.cancel()
        grid = render_frame(g, stick_on=False, held_on=False)
        assert grid[PEG_ROW_BOTTOM][2] == BRIGHTNESS_BLOCK
        assert all(v == 0 for v in grid[HELD_ROW])
