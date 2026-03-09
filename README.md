# microbit-hanoi

A Tower of Hanoi game for the BBC micro:bit V2, written in MicroPython.

## Game overview

Move all the blocks from the leftmost peg to the rightmost peg, one block at a
time, without ever placing a larger block on top of a smaller one.

There are four levels:

| Level | Blocks to move | Min. moves |
|-------|---------------|------------|
| 1     | 1             | 1          |
| 2     | 2             | 3          |
| 3     | 3             | 7          |
| 4     | 4             | 15         |

Completing level 4 loops back to level 1.

## Display

The game world is wider than the 5×5 LED display.  The view scrolls
horizontally to reveal all three pegs.

Blocks are displayed as horizontal bars of 1, 3, 5, or 7 LEDs (odd widths so
they sit symmetrically on a peg).  The 7-wide block is larger than the 5-wide
display; when centred on a peg its two edge pixels fold upward into the row
above the block (a "bend-around-the-top" effect).

Peg separation grows with each level so that adjacent blocks cannot overlap
(`separation = 2 × level`).  On level 1 the pegs are only 2 columns apart and
all three fit on-screen at once; by level 4 they are 8 columns apart, requiring
scrolling to see each peg.

**Brightness levels:**
- Pegs (sticks): dim, rapid blinking to give a faded appearance
- Stacked blocks: always bright (full brightness)
- Held block: shown at the top of the display at medium brightness, blinking

## Controls

| Action                        | Control                    |
|-------------------------------|----------------------------|
| Scroll view left / right      | Tilt device right / left   |
| Pick up top block (or place)  | Button B (right button)    |
| Cancel pick-up                | Button A (left button)     |

**Scrolling:** tilt the device so gravity would cause the world to slide — tilt
left to slide the world to the right (revealing the right pegs), and vice versa.
Larger tilts scroll faster.

**Picking up / placing:** scroll until the target peg is roughly centred on the
display, then press **B**.  The selected peg is whichever peg is closest to the
screen centre.  While holding a block it floats at the top of the display; press
**A** at any time to cancel and return it to its original peg.

When a level is complete a star flashes and a victory tune plays before the next
level begins.

## Flashing to the micro:bit

Two files must be transferred: `hanoi_logic.py` (game logic) and `main.py`
(entry point).  Flash `hanoi_logic.py` first so that `main.py` can import it.

### Option 1 — `ufs` (command-line)

[`ufs`](https://github.com/ntoll/microfs) is a small utility for transferring
files to a micro:bit over USB.

```bash
pip install microfs
ufs put hanoi_logic.py
ufs put main.py
```

After flashing, press the reset button on the back of the micro:bit.

### Option 2 — `mpremote`

```bash
pip install mpremote
mpremote cp hanoi_logic.py :
mpremote cp main.py :
mpremote reset
```

### Option 3 — Mu Editor (GUI)

1. Open [Mu Editor](https://codewith.mu/) and select the **BBC micro:bit** mode.
2. Open `hanoi_logic.py` and click **Flash**.
3. Open `main.py` and click **Flash**.

### Option 4 — micro:bit Python online editor

1. Go to <https://python.microbit.org/>.
2. Use **Project → Create file** to add `hanoi_logic.py` and paste its contents.
3. Paste the contents of `main.py` into the main editor pane.
4. Click **Send to micro:bit**.

## Running the tests (no hardware required)

`hanoi_logic.py` has no micro:bit dependencies and can be tested with standard
Python:

```bash
pip install pytest
pytest test_hanoi.py -v
```

All 92 tests should pass.

## File structure

| File             | Purpose                                              |
|------------------|------------------------------------------------------|
| `main.py`        | Entry point; runs on the micro:bit                   |
| `hanoi_logic.py` | Pure-Python game logic (importable on PC for tests)  |
| `test_hanoi.py`  | pytest unit tests — no hardware needed               |

## Technical notes

- Tested with micro:bit V2 running **MicroPython v1.13** (firmware 0257).
- Uses `music.POWER_UP` for the victory jingle; does not rely on `audio.Sound`,
  which is absent from older firmware builds.
- Uses a custom `Image` string for the victory star rather than `Image.STAR`,
  which is not available in all firmware versions.
