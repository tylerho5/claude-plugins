#!/usr/bin/env bash
# Print the absolute path to the Claude Code native (Bun-compiled) executable,
# regardless of install method. Exits 1 if no native binary is found.
#
# Why this exists: the binary lives in a different place per install method, and
# some wrappers on PATH are shims/launchers, not the binary itself. Never hardcode
# a path — resolve, then confirm the target is actually a native executable.
set -uo pipefail

is_native() { file -b "$1" 2>/dev/null | grep -qE 'Mach-O|ELF|PE32'; }

resolve() {  # follow symlinks portably (BSD readlink lacks -f on older macOS)
  if readlink -f "$1" >/dev/null 2>&1; then readlink -f "$1"
  else python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$1"; fi
}

candidates() {
  command -v claude 2>/dev/null                              # whatever PATH resolves (may be a shim)
  echo "$HOME/.local/bin/claude"                             # native installer launcher
  ls -1 "$HOME"/.local/share/claude/versions/* 2>/dev/null   # native installer versions
  local nr; nr="$(npm root -g 2>/dev/null || true)"          # npm global: real binary is in a platform pkg
  if [ -n "$nr" ]; then
    ls -1 "$nr"/@anthropic-ai/claude-code-*/claude 2>/dev/null
    echo "$nr/@anthropic-ai/claude-code/bin/claude.exe"      # postinstall copies the binary here
  fi
  find "$HOME/.claude/local" -name 'claude*' -type f 2>/dev/null  # legacy migrate-installer
}

seen="|"
while IFS= read -r c; do
  [ -n "$c" ] || continue
  r="$(resolve "$c" 2>/dev/null)" || continue
  case "$seen" in *"|$r|"*) continue;; esac
  seen="$seen$r|"
  if is_native "$r"; then echo "$r"; exit 0; fi
done < <(candidates)

echo "No native Claude Code binary found on PATH or in known install locations." >&2
echo "If installed via 'npm --ignore-scripts' or '--omit=optional', the binary sits in an" >&2
echo "@anthropic-ai/claude-code-<platform> package; reinstall without those flags, or run 'npm rebuild'." >&2
exit 1
