---
name: datamining-claude-code-binary
description: >-
  Use when you need to inspect, reverse-engineer, or extract something from the
  Claude Code native binary itself — embedded system prompts, tool definitions,
  feature-flag (tengu_*) gates, telemetry event names, or other internal machinery
  — regardless of how Claude Code was installed. Triggers on "what's baked into the
  CC binary", "find the embedded prompt/string", "extract the system prompt", "spelunk
  / datamine the claude binary", or needing to locate the compiled executable across
  install methods (native installer, npm, Homebrew).
---

# Datamining the Claude Code Binary

Claude Code ships as a **Bun-compiled single-file native executable** (Mach-O on
macOS, ELF on Linux, PE on Windows), ~250MB+. The application code is embedded as
**minified-but-readable UTF-8 JavaScript** — one giant line, no newlines. So the
whole exercise is two steps: **locate the native binary** (install-agnostic), then
**carve byte windows** out of it (line-based grep context is useless).

## Step 1: Locate the binary (never hardcode the path)

The install method decides *where* the binary lives — but every method produces the
*same* Bun-compiled native executable, so the carving technique is identical once you
have it. Resolve it, don't assume it.

The two helpers live in this skill's `scripts/` dir. You'll be investigating a binary
elsewhere, not sitting in the skill folder, so point `$SK` at that dir's absolute path
(the directory holding this SKILL.md, `+ /scripts`) and call the helpers through it:

```bash
SK="<abs path to this skill>/scripts"       # e.g. ~/.claude/skills/datamining-claude-code-binary/scripts
BIN="$("$SK"/locate-claude-binary.sh)"      # prints the native binary path, or exits 1
file "$BIN"                                  # confirm: Mach-O / ELF / PE, not a script
```

Why a helper instead of a fixed path — locations by install method:

| Install method | Native binary location |
|---|---|
| Native installer | `~/.local/share/claude/versions/<ver>` (symlinked from `~/.local/bin/claude`) |
| npm global | `$(npm root -g)/@anthropic-ai/claude-code-<platform>/claude`, copied over `.../claude-code/bin/claude.exe` |
| Homebrew / Windows native | same Bun binary (PE on Windows), path per that tool's prefix |

Gotchas the locator handles: the thing on `PATH` may be a wrapper/shim that re-execs
`claude` (harness launchers, the npm `cli-wrapper.cjs`), so resolve symlinks and
confirm with `file`. `~/.claude.json`'s `installMethod` field is a useful hint
(`native`/`global`), but it's a label, not a path — always resolve-and-`file`. An npm
install done with `--ignore-scripts`/`--omit=optional` leaves only a ~500-byte JS stub
at the `claude` path; the real binary is then inside the `@anthropic-ai/claude-code-<platform>`
optional-dependency package (the locator checks there too).

## Step 2: two different jobs — enumerate vs. carve

**To enumerate identifiers** (list every flag/event/tool name of a shape), filter the
whole binary — no offsets, no window sizing. `strings` splits on non-printable bytes, so
each identifier comes out clean:

```bash
LC_ALL=C strings -n 8 "$BIN" | grep -oE 'tengu_[a-z0-9_]+' | sort -u   # ~1700+ names
```

**To read machinery** (the code/prose around a specific hit), carve a byte window. The
embedded JS is one line, so `grep -A/-B` context does nothing — carve instead:

```bash
LC_ALL=C grep -a -b -o "MARKER" "$BIN" | head              # byte offsets, no python
scripts="$SK"/carve.py                                     # (from Step 1)
"$scripts" "$BIN" --find 'MARKER'                          # lists offsets + "(showing N of M)"
OFF=$("$scripts" "$BIN" --find 'MARKER' --limit 1)
"$scripts" "$BIN" --at "$OFF" --len 4000 --back 500
```

Windows hold raw bytes — pipe through a printable filter to read them. **Widen `--len`
if the thing you want is cut off; start ~4KB and go up.**

```bash
"$scripts" "$BIN" --at "$OFF" --len 4000 | LC_ALL=C tr -c '[:print:]\n' '.'
# or: ... | LC_ALL=C strings -n 6
```

Always `LC_ALL=C` — otherwise `tr`/`grep`/`strings` throw "Illegal byte sequence" on
non-UTF8 bytes. A given marker can appear at several offsets, and **not all land in the
JS blob** — some fall in packed data/UTF-16 tables and carve to garbage (repeated bytes,
no ASCII words). If a window is unreadable, carve the *next* offset in the list, not just
a nudged `--at`. Within a single readable window, UTF-16 (chars space-interleaved) and
plain single-byte JS often coexist; `strings` pulls readable runs out of both.

### No seed phrase? Discover readable prose cold

To find embedded English (prompt text, tool descriptions) when you have nothing to grep
for yet, pull out capitalized sentences directly:

```bash
LC_ALL=C grep -a -o -E '[A-Z][a-z]+( [a-zA-Z]+){6,}[.?]' "$BIN" | sort -u | less
```

Then grep a distinctive fragment of a hit and carve its window for surrounding context.

## What lives in there

- **Feature flags:** GrowthBook `tengu_*` gates. `tengu_*` is also used for **telemetry
  event names** — a bare string match doesn't tell you which (a match is not a use). The
  tell is the call shape: a flag is *read* through a 2–3-char gate helper that takes a
  **default value** as its second arg — `Qe("tengu_amber_flint",!0)` (`!1`=default false,
  `!0`=default true; defaults can also be `null`, a number, a string, or a variable).
  Telemetry is *emitted* through a different (often 1-char) helper whose second arg is an
  **object** — `N("tengu_advisor_dialog_shown",{...})`. So enumerate flags by matching a
  short call whose second arg is anything but `{`:

  ```bash
  LC_ALL=C grep -a -o -E '[A-Za-z$_]{2,3}\("tengu_[a-z0-9_]+",[^{]' "$BIN" \
    | grep -oE 'tengu_[a-z0-9_]+' | sort -u
  ```

  This is approximate — the helper's minified name **drifts between builds** (`Ke`, `Qe`,
  …), so don't grep the name; and a stray telemetry call with a variable payload can slip
  in. To *prove* a specific name is a flag, carve its call-site and confirm the return
  value is branched on (gate) rather than fired and dropped (telemetry).
- **Prompts / tool definitions / machinery:** grep a distinctive phrase you expect
  (a tool name, an error string), then carve the surrounding window.

## Big investigations: fan out

For anything spanning many subsystems, dispatch parallel general-purpose subagents,
each carving a different area. They have Bash and reads are safe; tell them to add
`dangerouslyDisableSandbox` if a read is sandbox-blocked, and give each the `$BIN`
path so they skip re-discovery.

## Common mistakes

- **Hardcoding `~/.local/share/claude/versions/<ver>`** — only correct for the native
  installer. Run the locator instead.
- **Assuming the `claude` on PATH is the binary** — it's often a shim. Resolve + `file`.
- **Using `grep -A/-B` for context** — the JS is one line; context flags do nothing.
  Carve byte windows.
- **Carving windows to build a *list*** — that's slow and misses sparse hits. Enumerate
  with `strings | grep | sort -u`; reserve carving for reading context around one hit.
- **Reading windows without `LC_ALL=C`** — byte-sequence errors on macOS.
