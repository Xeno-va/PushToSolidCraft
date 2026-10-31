# Push to SolidCraft

A button in KiCad's board editor that sends the board to [SolidCraft](https://github.com/tangency-labs/solidcraft)
in one click, the way Eagle could push a board to Fusion. The board opens in a new SolidCraft
tab looking like the real thing: solder mask, silkscreen, top and bottom traces, pads, holes and
every component with a 3D model. One way only: nothing comes back to KiCad.

**Works on Linux** (built and tested there). macOS and Windows are untested.

The board, traces, mask and silkscreen are light display surfaces, not solid bodies, so a board
stays quick to work with when it is a small part of a larger mechanical design. Only the bare
board is a true solid you can measure and attach to.

On a 100-part, two-sided board with KiCad 10.0.6 and SolidCraft 0.28 on Linux: about 8 seconds
from the click to the open tab.

## What one click does

1. **Saves the board**, the same as pressing Save. Edits you have not saved could not be sent
   otherwise.
2. **Converts it** with [solidcraft-kicad](https://github.com/fpoussin/solidcraft-kicad), off
   KiCad's thread so the editor stays responsive.
3. **Opens it in SolidCraft** as a new, read-only tab: in the window you already have open, or
   it starts SolidCraft. Use Save As to keep a copy. Each push opens a fresh tab, because
   SolidCraft cannot reload or close a tab from outside; close old ones yourself.
4. **Makes a drop-in copy**: one light mesh file with every colour, for dropping the board into
   another design with Insert Mesh. It takes about 25 seconds more and inserts in under a
   second. (Linking the saved board design into another design brings only the bare board
   across, not the traces and parts, which is why this copy exists.)

Both files go in a `solidcraft` folder next to the board, with a log of the last push.
Progress and errors appear as desktop notifications.

## Needs

- **KiCad 10**, with `kicad-cli` on the PATH.
- **SolidCraft** 0.18.3 or later (tested with 0.28.0), with its control channel on (the default).
- **[solidcraft-kicad](https://github.com/fpoussin/solidcraft-kicad/releases)** (tested with
  0.4.0): the converter, by another author. This button only drives it.
- Python 3 on the PATH.

Tested on Linux (Fedora, KDE). macOS and Windows paths are in the code but untested, and the
installer is for Linux only.

## Install

```
git clone https://github.com/Xeno-va/PushToSolidCraft.git
cd PushToSolidCraft
./install.sh
```

Restart the board editor. The button is the green board with a blue arrow, at the right end of
the top toolbar.

The programs are found on the PATH, then in usual install folders (`~/Applications`, an
extracted SolidCraft in `~/.local/share/solidcraft-*`). To point at them directly, set
`SOLIDCRAFT_KICAD`, `SOLIDCRAFT_APP` and `SOLIDCRAFT_CLI`.

## Known limits

- Inner copper layers are not shown (solidcraft-kicad leaves them out).
- solidcraft-kicad 0.4.0 stops on boards whose logo graphics have references like `G***`
  (seen on SparkFun boards).
- Parts with no 3D model in KiCad come across without a body, as they should.

## License

MIT. solidcraft-kicad is Apache-2.0 and SolidCraft is MIT or Apache-2.0; neither is included
here. This project is not affiliated with either.
