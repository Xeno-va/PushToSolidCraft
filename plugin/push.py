"""Send a saved KiCad board to SolidCraft.

Runs outside KiCad so the editor stays responsive. Writes, next to the board,
a folder `solidcraft/` holding:
  <board>.solidcraft  the board as its own design; a read-only copy of it
                      opens in a new tab (Save As to keep it elsewhere)
  <board>.3mf         one light mesh with every colour, for dropping into
                      other designs (Insert Mesh); a linked design would bring
                      only the bare board across, not the traces and parts
Progress and failures go to desktop notifications and solidcraft/push.log.
"""

import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOME = Path.home()

if sys.platform == "darwin":
    CONTROL = HOME / "Library/Application Support/SolidCraft/control"
    CACHE = HOME / "Library/Caches/push-to-solidcraft"
elif os.name == "nt":
    CONTROL = Path(os.environ.get("LOCALAPPDATA", HOME)) / "SolidCraft/control"
    CACHE = Path(os.environ.get("LOCALAPPDATA", HOME)) / "push-to-solidcraft/cache"
else:
    data = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
    CONTROL = data / "solidcraft/control"
    CACHE = Path(os.environ.get("XDG_CACHE_HOME", HOME / ".cache")) / "push-to-solidcraft"
CONTROL = Path(os.environ.get("SOLIDCRAFT_CONTROL_DIR", CONTROL))


def newest(*patterns):
    found = [p for pattern in patterns for p in glob.glob(str(HOME / pattern))]
    found.sort(key=lambda p: [int(n) for n in re.findall(r"\d+", p)])
    return Path(found[-1]) if found else None


def find(env, name, *patterns):
    """A program: from its environment variable, the PATH, then usual places."""
    if os.environ.get(env):
        return Path(os.environ[env])
    on_path = shutil.which(name)
    return Path(on_path) if on_path else newest(*patterns)


IMPORTER = find("SOLIDCRAFT_KICAD", "solidcraft-kicad",
                "Applications/solidcraft-kicad", ".local/bin/solidcraft-kicad")
APP = find("SOLIDCRAFT_APP", "solidcraft",
           ".local/share/solidcraft-*/usr/bin/solidcraft",
           "Applications/solidcraft-*.AppImage")
CLI = find("SOLIDCRAFT_CLI", "solidcraft-cli",
           ".local/share/solidcraft-*/usr/bin/solidcraft-cli")


def notify(text, urgent=False):
    if shutil.which("notify-send"):
        subprocess.run(["notify-send", "-a", "KiCad", "-u", "critical" if urgent else "normal",
                        "Push to SolidCraft", text], check=False)
    elif sys.platform == "darwin":
        subprocess.run(["osascript", "-e",
                        f"display notification {json.dumps(text)} with title \"Push to SolidCraft\""],
                       check=False)


def running_app():
    """(port, token) of the open SolidCraft window, or None."""
    try:
        port = int((CONTROL / "current.port").read_text().strip())
        token = (CONTROL / f"{port}.token").read_text().strip()
        socket.create_connection(("127.0.0.1", port), timeout=1).close()
        return port, token
    except (OSError, ValueError):
        return None


def tell_app(port, token, path):
    with socket.create_connection(("127.0.0.1", port), timeout=120) as s:
        msg = {"id": 1, "token": token, "method": "engine.execute",
               "params": {"command": "doc.open",
                          "params": {"path": str(path), "read_only": True}}}
        s.sendall((json.dumps(msg) + "\n").encode())
        reply = json.loads(s.makefile("r").readline())
    if not reply.get("ok"):
        raise RuntimeError(f"SolidCraft refused the board: {reply.get('error')}")


def main(board):
    board = Path(board).resolve()
    out = board.parent / "solidcraft"
    out.mkdir(exist_ok=True)
    design = out / f"{board.stem}.solidcraft"
    mesh = out / f"{board.stem}.3mf"
    log = open(out / "push.log", "w")

    def run(args):
        log.write("$ " + " ".join(map(str, args)) + "\n"); log.flush()
        r = subprocess.run(list(map(str, args)), stdout=log, stderr=log)
        if r.returncode:
            raise RuntimeError(f"{Path(args[0]).name} failed; see {out / 'push.log'}")

    try:
        if not IMPORTER or not IMPORTER.exists():
            raise RuntimeError("solidcraft-kicad was not found: put it on the PATH "
                               "or set SOLIDCRAFT_KICAD to it.")
        start = time.monotonic()
        notify(f"Sending {board.stem}…")
        run([IMPORTER, "build", "--no-update-check", "-f", "-o", design, board])

        # SolidCraft only switches to a tab already showing a file, never
        # reloads it, so each push opens its own copy in a new tab.
        CACHE.mkdir(parents=True, exist_ok=True)
        for old in CACHE.glob("*.solidcraft"):
            if time.time() - old.stat().st_mtime > 86400:
                old.unlink(missing_ok=True)
        shown = CACHE / f"{board.stem} {time.strftime('%H%M%S')}.solidcraft"
        shutil.copyfile(design, shown)

        found = running_app()
        if found:
            tell_app(*found, shown)
        elif APP:
            subprocess.Popen([APP, shown], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            raise RuntimeError(f"SolidCraft was not found; the board is in {design}")
        notify(f"{board.stem} is open in SolidCraft "
               f"({time.monotonic() - start:.0f} s). Making the drop-in copy…")

        if not CLI:
            notify("solidcraft-cli was not found, so no drop-in copy was made.")
            return
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as script:
            json.dump([{"command": "file.export", "params": {"path": str(mesh)}}], script)
        try:
            run([CLI, "run", script.name, "--in", design, "--quiet"])
        finally:
            os.unlink(script.name)
        notify(f"Drop-in copy ready: {mesh.name}, beside the board in its solidcraft folder.")
    except Exception as e:
        log.write(f"\n{e}\n")
        notify(str(e), urgent=True)
        sys.exit(1)
    finally:
        log.close()


if __name__ == "__main__":
    main(sys.argv[1])
