"""
Tower of Hanoi for micro:bit V2 – main entry point.

Controls:
  Tilt left   – scroll right (see more of the right side of the world)
  Tilt right  – scroll left  (see more of the left side of the world)
  Button B    – pick up the top block from the selected peg /
                place the held block on the selected peg
  Button A    – cancel: return the held block to where it came from

The world is 15 columns wide; the display shows a 5-column window.
Pegs are at world columns 2, 7, 12 (left, middle, right).

Levels 1-4 require moving 1, 2, 3, 4 blocks from the leftmost peg to
the rightmost peg.  After level 4 the game loops back to level 1.
"""

from microbit import display, button_a, button_b, accelerometer, Image
import audio
import utime
import hanoi_logic

# ── Timing (milliseconds) ─────────────────────────────────────────────────
LOOP_MS        = 20    # target loop period (~50 Hz)
STICK_BLINK_MS = 120   # stick on/off half-period  (~8 Hz)
HELD_BLINK_MS  = 160   # held-block on/off half-period (~6 Hz)

# ── Blink state ───────────────────────────────────────────────────────────
_stick_timer = 0
_stick_on    = True
_held_timer  = 0
_held_on     = True


def _grid_to_image(grid):
    """Convert a 5×5 brightness grid to a micro:bit Image."""
    return Image(':'.join(''.join(str(v) for v in row) for row in grid))


def _show_victory():
    """Flash a star and play a congratulatory sound."""
    try:
        audio.play(audio.Sound.HAPPY, wait=False)
    except Exception:
        try:
            audio.play(audio.Sound.SPRING, wait=False)
        except Exception:
            pass

    # Flash star three times then hold
    for _ in range(3):
        display.show(Image.STAR)
        utime.sleep_ms(200)
        display.clear()
        utime.sleep_ms(150)

    display.show(Image.STAR)
    utime.sleep_ms(1200)
    display.clear()


def _reset_blink():
    global _stick_timer, _stick_on, _held_timer, _held_on
    _stick_timer = 0
    _stick_on    = True
    _held_timer  = 0
    _held_on     = True


def main():
    global _stick_timer, _stick_on, _held_timer, _held_on

    game     = hanoi_logic.GameState()
    last_ms  = utime.ticks_ms()

    while True:
        now_ms = utime.ticks_ms()
        dt     = utime.ticks_diff(now_ms, last_ms)
        last_ms = now_ms

        # ── Input ──────────────────────────────────────────────────────
        ax = accelerometer.get_x()
        game.update_scroll(ax, dt)

        if button_b.was_pressed():   # right button: pick up / place
            game.action()

        if button_a.was_pressed():   # left button: cancel
            game.cancel()

        # ── Win check ──────────────────────────────────────────────────
        if game.is_level_complete():
            _show_victory()
            game.next_level()
            _reset_blink()
            last_ms = utime.ticks_ms()
            continue

        # ── Blink state update ─────────────────────────────────────────
        _stick_timer += dt
        if _stick_timer >= STICK_BLINK_MS:
            _stick_timer -= STICK_BLINK_MS
            _stick_on = not _stick_on

        _held_timer += dt
        if _held_timer >= HELD_BLINK_MS:
            _held_timer -= HELD_BLINK_MS
            _held_on = not _held_on

        # ── Render ─────────────────────────────────────────────────────
        grid = hanoi_logic.render_frame(game, _stick_on, _held_on)
        display.show(_grid_to_image(grid))

        # ── Maintain loop rate ─────────────────────────────────────────
        elapsed    = utime.ticks_diff(utime.ticks_ms(), now_ms)
        sleep_time = LOOP_MS - elapsed
        if sleep_time > 0:
            utime.sleep_ms(sleep_time)


main()
