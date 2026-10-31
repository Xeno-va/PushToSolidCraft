#!/usr/bin/env bash
# Put the Push to SolidCraft button into KiCad's board editor.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

installed=0
for base in "$HOME/.local/share/kicad" "$HOME/.var/app/org.kicad.KiCad/data/kicad"; do
  for ver in "$base"/1[0-9].*; do
    [ -d "$ver" ] || continue
    mkdir -p "$ver/scripting/plugins"
    ln -sfn "$HERE/plugin" "$ver/scripting/plugins/push-to-solidcraft"
    echo "Installed for KiCad $(basename "$ver") in $ver/scripting/plugins"
    installed=1
  done
done
[ "$installed" = 1 ] || { echo "No KiCad 10 settings folder found. Open KiCad 10 once, then run this again."; exit 1; }

command -v kicad-cli >/dev/null || echo "Warning: kicad-cli is not on the PATH; the importer needs it."
if ! command -v solidcraft-kicad >/dev/null && [ -z "${SOLIDCRAFT_KICAD:-}" ] && [ ! -x "$HOME/Applications/solidcraft-kicad" ]; then
  echo "Warning: solidcraft-kicad was not found. Download it from"
  echo "  https://github.com/fpoussin/solidcraft-kicad/releases"
  echo "and put it on the PATH (or in ~/Applications)."
fi
echo "Restart the KiCad board editor; the button is at the right end of the top toolbar."
