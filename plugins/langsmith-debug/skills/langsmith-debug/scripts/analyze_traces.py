#!/usr/bin/env python3
"""
Consolidated LangSmith trace analysis tool.

Subcommands:
    summary <input>  — Cross-trace stats and pattern detection
    compare <input>   — Success vs failure diff, or two specific files
    errors <input>    — Group and correlate errors

Input: .jsonl file, .json file, directory of .json/.jsonl files, or two files for compare.
"""

import json
import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Input loading — supports .json, .jsonl (langsmith trace export), directories
# ---------------------------------------------------------------------------

def _parse_jsonl(path: Path) -> List[Dict]:
    """Parse JSONL where each line is a run; group by trace_id into traces."""
    runs_by_trace: Dict[str, List[Dict]] = defaultdict(list)

    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                run = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: {path.name} line {lineno}: {e}", file=sys.stderr)
                continue
            tid = run.get("trace_id") or run.get("id", "unknown")
            runs_by_trace[tid].append(run)

    traces = []
    for trace_id, runs in runs_by_trace.items():
        root = _build_trace_from_runs(trace_id, runs)
        traces.append(root)
    return traces


def _build_trace_from_runs(trace_id: str, runs: List[Dict]) -> Dict:
    """Reconstruct a trace dict from flat JSONL runs using parent_run_id."""
    root_run = None
    for r in runs:
        if not r.get("parent_run_id"):
            root_run = r
            break
    if root_run is None and runs:
        root_run = runs[0]

    total_tokens = 0
    total_cost = 0.0
    has_error = False
    start_times, end_times = [], []
    flat_runs = []

    for r in runs:
        if r.get("error"):
            has_error = True

        usage = r.get("token_usage") or r.get("usage") or {}
        total_tokens += usage.get("total_tokens", 0)
        total_cost += r.get("cost", 0.0)

        for field, target in [("start_time", start_times), ("end_time", end_times)]:
            ts = r.get(field)
            if ts:
                target.append(ts)

        flat_runs.append({
            "id": r.get("run_id", r.get("id")),
            "name": r.get("name", "unknown"),
            "run_type": r.get("run_type", "unknown"),
            "error": r.get("error"),
            "error_type": r.get("error_type"),
            "start_time": r.get("start_time"),
            "end_time": r.get("end_time"),
            "inputs": r.get("inputs"),
            "outputs": r.get("outputs"),
            "stack_trace": r.get("stack_trace", ""),
            "parent_run_id": r.get("parent_run_id"),
        })

    duration_ms = None
    if start_times and end_times:
        try:
            earliest = min(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in start_times)
            latest = max(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in end_times)
            duration_ms = (latest - earliest).total_seconds() * 1000
        except Exception:
            pass

    trace = {
        "id": trace_id,
        "name": (root_run or {}).get("name", "unknown"),
        "run_type": (root_run or {}).get("run_type", "chain"),
        "error": (root_run or {}).get("error") if has_error else None,
        "error_type": (root_run or {}).get("error_type"),
        "runs": flat_runs,
        "total_tokens": total_tokens,
        "total_cost": total_cost if total_cost else None,
        "start_time": min(start_times) if start_times else None,
        "end_time": max(end_times) if end_times else None,
    }
    if duration_ms is not None:
        trace["duration_ms"] = duration_ms

    return trace


def _parse_json(path: Path) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return [data]


def load_input(path_str: str) -> List[Dict]:
    """Auto-detect format and load traces."""
    p = Path(path_str)
    if not p.exists():
        print(f"Error: not found: {p}", file=sys.stderr)
        sys.exit(1)

    if p.is_dir():
        traces = []
        for f in sorted(p.iterdir()):
            if f.suffix == ".jsonl":
                traces.extend(_parse_jsonl(f))
            elif f.suffix == ".json":
                traces.extend(_parse_json(f))
        return traces

    if p.suffix == ".jsonl":
        return _parse_jsonl(p)
    if p.suffix == ".json":
        return _parse_json(p)

    print(f"Error: unsupported file type: {p.suffix}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _calc_stats(values: List[float]) -> Dict:
    if not values:
        return {}
    s = sorted(values)
    n = len(s)
    return {
        "min": s[0],
        "max": s[-1],
        "avg": sum(s) / n,
        "p50": s[n // 2],
        "p95": s[int(n * 0.95)] if n >= 2 else s[-1],
        "total": sum(s),
    }


def _trace_has_error(trace: Dict) -> bool:
    if trace.get("error"):
        return True
    return any(r.get("error") for r in trace.get("runs", []))


def _trace_duration_s(trace: Dict) -> Optional[float]:
    if "duration_ms" in trace:
        return trace["duration_ms"] / 1000
    if trace.get("start_time") and trace.get("end_time"):
        try:
            s = datetime.fromisoformat(trace["start_time"].replace("Z", "+00:00"))
            e = datetime.fromisoformat(trace["end_time"].replace("Z", "+00:00"))
            return (e - s).total_seconds()
        except Exception:
            return None
    return None


def _short_id(trace_id: str) -> str:
    return trace_id[:5] if trace_id and len(trace_id) >= 5 else trace_id


def _fmt_duration(sec: float) -> str:
    return f"{sec:.1f}s"


def _fmt_tokens(n: float) -> str:
    if n >= 1000:
        return f"{n:,.0f}"
    return f"{n:.0f}"


# ---------------------------------------------------------------------------
# SUMMARY subcommand
# ---------------------------------------------------------------------------

def cmd_summary(traces: List[Dict], verbose: bool, as_json: bool):
    n = len(traces)
    success = [t for t in traces if not _trace_has_error(t)]
    failed = [t for t in traces if _trace_has_error(t)]
    error_rate = len(failed) / n if n else 0

    durations = [d for t in traces if (d := _trace_duration_s(t)) is not None]
    dur_stats = _calc_stats(durations)

    token_vals = [t["total_tokens"] for t in traces if t.get("total_tokens")]
    tok_stats = _calc_stats(token_vals)

    error_types: Dict[str, List[str]] = defaultdict(list)
    for t in failed:
        tid = _short_id(t.get("id", "?"))
        if t.get("error"):
            error_types[t.get("error_type", "Unknown")].append(tid)
        for r in t.get("runs", []):
            if r.get("error"):
                etype = r.get("error_type", "Unknown")
                if tid not in error_types[etype]:
                    error_types[etype].append(tid)

    patterns = _detect_patterns(traces)

    if as_json:
        print(json.dumps({
            "traces": n, "success": len(success), "failed": len(failed),
            "error_rate": error_rate,
            "duration": dur_stats, "tokens": tok_stats,
            "error_types": {k: v for k, v in error_types.items()},
            "patterns": patterns,
        }, indent=2))
        return

    print(f"Analyzed {n} traces ({len(success)} success, {len(failed)} failed) — {error_rate:.1%} error rate")

    if dur_stats:
        print(f"Duration: avg {_fmt_duration(dur_stats['avg'])}, p50 {_fmt_duration(dur_stats['p50'])}, p95 {_fmt_duration(dur_stats['p95'])}")
    if tok_stats:
        print(f"Tokens: avg {_fmt_tokens(tok_stats['avg'])}, total {_fmt_tokens(tok_stats['total'])}")

    if error_types:
        sorted_errors = sorted(error_types.items(), key=lambda x: len(x[1]), reverse=True)
        limit = len(sorted_errors) if verbose else 3
        print(f"\nErrors ({len(sorted_errors)} types):")
        for etype, tids in sorted_errors[:limit]:
            id_list = ", ".join(tids[:5])
            suffix = f" +{len(tids)-5} more" if len(tids) > 5 else ""
            label = "trace" if len(tids) == 1 else "traces"
            print(f"  {etype}: {len(tids)} {label} [{id_list}{suffix}]")
        if not verbose and len(sorted_errors) > 3:
            print(f"  ... +{len(sorted_errors)-3} more (use --verbose)")

    if patterns:
        print("\nPatterns:")
        limit = len(patterns) if verbose else 5
        for p in patterns[:limit]:
            print(f"  - {p}")


def _detect_patterns(traces: List[Dict]) -> List[str]:
    patterns = []

    tool_calls: Dict[str, Dict] = defaultdict(lambda: {"ok": 0, "fail": 0})
    for t in traces:
        for r in t.get("runs", []):
            if r.get("run_type") == "tool":
                name = r.get("name", "unknown")
                if r.get("error"):
                    tool_calls[name]["fail"] += 1
                else:
                    tool_calls[name]["ok"] += 1

    for name, counts in tool_calls.items():
        total = counts["ok"] + counts["fail"]
        if total >= 3 and counts["fail"] / total >= 0.3:
            pct = counts["fail"] / total * 100
            patterns.append(
                f'Tool "{name}" fails in {pct:.0f}% of calls ({counts["fail"]}/{total})'
            )

    run_counts_ok = []
    run_counts_fail = []
    for t in traces:
        rc = len([r for r in t.get("runs", []) if r.get("run_type") == "tool"])
        if _trace_has_error(t):
            run_counts_fail.append(rc)
        else:
            run_counts_ok.append(rc)

    if run_counts_ok and run_counts_fail:
        avg_ok = sum(run_counts_ok) / len(run_counts_ok)
        avg_fail = sum(run_counts_fail) / len(run_counts_fail)
        if avg_ok > 0 and avg_fail / avg_ok >= 1.5:
            patterns.append(
                f"Failed traces avg {avg_fail:.1f} tool calls vs {avg_ok:.1f} for successes ({avg_fail/avg_ok:.1f}x)"
            )

    durations = [(t, _trace_duration_s(t)) for t in traces]
    durations = [(t, d) for t, d in durations if d is not None]
    if len(durations) >= 3:
        avg_d = sum(d for _, d in durations) / len(durations)
        if avg_d > 0:
            for t, d in sorted(durations, key=lambda x: x[1], reverse=True)[:3]:
                if d > avg_d * 3:
                    tid = _short_id(t.get("id", "?"))
                    patterns.append(
                        f"Duration outlier: trace {tid} at {_fmt_duration(d)} ({d/avg_d:.1f}x avg)"
                    )

    return patterns


# ---------------------------------------------------------------------------
# COMPARE subcommand
# ---------------------------------------------------------------------------

def cmd_compare(inputs: List[str], verbose: bool, as_json: bool):
    if len(inputs) == 2 and Path(inputs[0]).is_file() and Path(inputs[1]).is_file():
        t1 = load_input(inputs[0])
        t2 = load_input(inputs[1])
        if not t1 or not t2:
            print("Error: could not load traces from one or both files", file=sys.stderr)
            sys.exit(1)
        _compare_two(t1[0], t2[0], verbose, as_json)
    else:
        traces = load_input(inputs[0])
        _compare_groups(traces, verbose, as_json)


def _compare_groups(traces: List[Dict], verbose: bool, as_json: bool):
    success = [t for t in traces if not _trace_has_error(t)]
    failed = [t for t in traces if _trace_has_error(t)]

    succ_stats = _group_stats(success)
    fail_stats = _group_stats(failed)
    diffs = _find_diffs(succ_stats, fail_stats)

    if as_json:
        print(json.dumps({
            "success_count": len(success), "failed_count": len(failed),
            "success_stats": succ_stats, "failed_stats": fail_stats,
            "differences": diffs,
        }, indent=2))
        return

    print(f"Comparing {len(success)} successful vs {len(failed)} failed traces\n")

    if not diffs:
        print("No significant differences found.")
        return

    print("Key differences:")
    for d in diffs:
        print(f"  {d['metric']}: success={d['success']} | failed={d['failed']}"
              + (f"  ({d['note']})" if d.get("note") else ""))

    if verbose:
        for label, stats in [("Successful", succ_stats), ("Failed", fail_stats)]:
            if not stats:
                continue
            print(f"\n{label} group:")
            if stats.get("avg_duration"):
                print(f"  Avg duration: {_fmt_duration(stats['avg_duration'])}")
            if stats.get("avg_tokens"):
                print(f"  Avg tokens: {_fmt_tokens(stats['avg_tokens'])}")
            if stats.get("top_tools"):
                print(f"  Top tools: {', '.join(f'{t}({c})' for t, c in stats['top_tools'][:5])}")
            if stats.get("top_errors"):
                print(f"  Top errors: {', '.join(f'{t}({c})' for t, c in stats['top_errors'][:5])}")


def _group_stats(traces: List[Dict]) -> Dict:
    if not traces:
        return {}
    durations = [d for t in traces if (d := _trace_duration_s(t)) is not None]
    tokens = [t["total_tokens"] for t in traces if t.get("total_tokens")]
    run_counts = [len(t.get("runs", [])) for t in traces]

    tool_counter = Counter()
    error_counter = Counter()
    for t in traces:
        for r in t.get("runs", []):
            if r.get("run_type") == "tool":
                tool_counter[r.get("name", "unknown")] += 1
            if r.get("error"):
                error_counter[r.get("error_type", "Unknown")] += 1

    return {
        "avg_duration": sum(durations) / len(durations) if durations else None,
        "avg_tokens": sum(tokens) / len(tokens) if tokens else None,
        "avg_runs": sum(run_counts) / len(run_counts) if run_counts else None,
        "top_tools": tool_counter.most_common(5),
        "top_errors": error_counter.most_common(5),
    }


def _find_diffs(succ: Dict, fail: Dict) -> List[Dict]:
    diffs = []
    if not succ or not fail:
        return diffs

    if succ.get("avg_duration") and fail.get("avg_duration"):
        sd, fd = succ["avg_duration"], fail["avg_duration"]
        if abs(sd - fd) > 1:
            ratio = fd / sd if sd > 0 else 0
            diffs.append({
                "metric": "avg duration",
                "success": _fmt_duration(sd),
                "failed": _fmt_duration(fd),
                "note": f"{ratio:.1f}x" if ratio > 1 else None,
            })

    if succ.get("avg_tokens") and fail.get("avg_tokens"):
        st, ft = succ["avg_tokens"], fail["avg_tokens"]
        if abs(st - ft) > 500:
            diffs.append({
                "metric": "avg tokens",
                "success": _fmt_tokens(st),
                "failed": _fmt_tokens(ft),
            })

    if succ.get("avg_runs") and fail.get("avg_runs"):
        sr, fr = succ["avg_runs"], fail["avg_runs"]
        if abs(sr - fr) > 1:
            diffs.append({
                "metric": "avg runs",
                "success": f"{sr:.1f}",
                "failed": f"{fr:.1f}",
            })

    succ_tools = set(dict(succ.get("top_tools", [])).keys())
    fail_tools = set(dict(fail.get("top_tools", [])).keys())
    fail_only = fail_tools - succ_tools
    if fail_only:
        diffs.append({
            "metric": "tools only in failures",
            "success": "—",
            "failed": ", ".join(sorted(fail_only)),
        })

    return diffs


def _compare_two(t1: Dict, t2: Dict, verbose: bool, as_json: bool):
    diffs = []

    for key in ["run_type", "name", "total_tokens", "duration_ms"]:
        v1, v2 = t1.get(key), t2.get(key)
        if v1 != v2:
            diffs.append({"field": key, "trace1": v1, "trace2": v2})

    runs1, runs2 = t1.get("runs", []), t2.get("runs", [])
    if len(runs1) != len(runs2):
        diffs.append({"field": "run_count", "trace1": len(runs1), "trace2": len(runs2)})

    divergence_idx = None
    for i, (r1, r2) in enumerate(zip(runs1, runs2)):
        if r1.get("name") != r2.get("name") or r1.get("run_type") != r2.get("run_type"):
            divergence_idx = i
            break
        if r1.get("error") != r2.get("error"):
            divergence_idx = i
            break

    if as_json:
        print(json.dumps({
            "trace1_id": t1.get("id"), "trace2_id": t2.get("id"),
            "differences": diffs,
            "divergence_step": divergence_idx,
        }, indent=2))
        return

    tid1, tid2 = _short_id(t1.get("id", "?")), _short_id(t2.get("id", "?"))
    print(f"Comparing trace {tid1} vs {tid2}\n")

    if not diffs and divergence_idx is None:
        print("No significant differences found.")
        return

    for d in diffs:
        print(f"  {d['field']}: {d['trace1']} vs {d['trace2']}")

    if divergence_idx is not None:
        r1_name = runs1[divergence_idx].get("name", "?")
        r2_name = runs2[divergence_idx].get("name", "?")
        print(f"\n  Divergence at step {divergence_idx}: {r1_name} vs {r2_name}")


# ---------------------------------------------------------------------------
# ERRORS subcommand
# ---------------------------------------------------------------------------

def cmd_errors(traces: List[Dict], group_by: str, verbose: bool, as_json: bool):
    errors = _extract_all_errors(traces)

    if not errors:
        print("No errors found.")
        return

    grouped = _group_errors(errors, group_by)
    patterns = _find_error_patterns(errors, traces)

    if as_json:
        print(json.dumps({
            "total_errors": len(errors),
            "unique_traces": len(set(e["trace_id"] for e in errors)),
            "groups": {k: v for k, v in grouped.items()},
            "patterns": patterns,
        }, indent=2, default=str))
        return

    unique_traces = len(set(e["trace_id"] for e in errors))
    print(f"Found {len(errors)} errors across {unique_traces} traces\n")

    sorted_groups = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)
    limit = len(sorted_groups) if verbose else 3
    print(f"Grouped by {group_by} ({len(sorted_groups)} groups):")
    for key, errs in sorted_groups[:limit]:
        trace_ids = sorted(set(_short_id(e["trace_id"]) for e in errs))
        id_preview = ", ".join(trace_ids[:5])
        suffix = f" +{len(trace_ids)-5}" if len(trace_ids) > 5 else ""
        print(f"  {key}: {len(errs)} errors in {len(trace_ids)} traces [{id_preview}{suffix}]")

        if verbose:
            for e in errs[:3]:
                msg = e["error_message"][:120]
                ctx_name = e.get("context", {}).get("run_name", "")
                ctx_str = f" (in {ctx_name})" if ctx_name else ""
                print(f"    - {msg}{ctx_str}")
            if len(errs) > 3:
                print(f"    ... +{len(errs)-3} more")

    if not verbose and len(sorted_groups) > 3:
        print(f"  ... +{len(sorted_groups)-3} more groups (use --verbose)")

    if patterns:
        print("\nPatterns:")
        for p in patterns[:5 if not verbose else len(patterns)]:
            print(f"  - {p}")


def _extract_all_errors(traces: List[Dict]) -> List[Dict]:
    errors = []
    for trace in traces:
        trace_id = trace.get("id", "unknown")

        if trace.get("error"):
            errors.append({
                "trace_id": trace_id,
                "level": "trace",
                "error_type": trace.get("error_type", "Unknown"),
                "error_message": str(trace["error"]),
                "timestamp": trace.get("start_time"),
                "context": {"name": trace.get("name"), "run_type": trace.get("run_type")},
            })

        for i, run in enumerate(trace.get("runs", [])):
            if not run.get("error"):
                continue
            ctx = {
                "run_index": i,
                "run_name": run.get("name"),
                "run_type": run.get("run_type"),
            }
            stack = run.get("stack_trace", "")
            if stack:
                m = re.search(r'File "([^"]+)", line (\d+)', stack)
                if m:
                    ctx["source_file"] = m.group(1)
                    ctx["source_line"] = m.group(2)

            errors.append({
                "trace_id": trace_id,
                "level": "run",
                "error_type": run.get("error_type", "Unknown"),
                "error_message": str(run["error"]),
                "timestamp": run.get("start_time"),
                "context": ctx,
            })

    return errors


def _group_errors(errors: List[Dict], group_by: str) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = defaultdict(list)

    if group_by == "trace":
        for e in errors:
            groups[_short_id(e["trace_id"])].append(e)
    elif group_by == "time":
        for e in errors:
            ts = e.get("timestamp")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    total_min = dt.hour * 60 + dt.minute
                    w_start = (total_min // 60) * 60
                    wh, wm = divmod(w_start, 60)
                    key = dt.strftime(f"%Y-%m-%d {wh:02d}:{wm:02d}")
                    groups[key].append(e)
                    continue
                except Exception:
                    pass
            groups["unknown_time"].append(e)
    else:
        for e in errors:
            groups[e["error_type"]].append(e)

    return dict(groups)


def _find_error_patterns(errors: List[Dict], traces: List[Dict]) -> List[str]:
    patterns = []

    type_counts = Counter(e["error_type"] for e in errors)
    for etype, count in type_counts.most_common(3):
        if count >= 3:
            patterns.append(f"{etype} recurs {count} times across traces")

    step_errors: Dict[int, int] = defaultdict(int)
    for e in errors:
        if e["level"] == "run":
            step = e.get("context", {}).get("run_index")
            if step is not None:
                step_errors[step] += 1
    for step, count in sorted(step_errors.items(), key=lambda x: x[1], reverse=True)[:2]:
        if count >= 3:
            patterns.append(f"Step {step} fails in {count} traces")

    time_groups = _group_errors(errors, "time")
    for window, errs in time_groups.items():
        if len(errs) >= 5 and window != "unknown_time":
            patterns.append(f"Burst of {len(errs)} errors around {window}")

    return patterns


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze LangSmith traces (summary, compare, errors)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # summary
    p_sum = sub.add_parser("summary", help="Cross-trace stats and pattern detection")
    p_sum.add_argument("input", help="JSONL/JSON file or directory")
    p_sum.add_argument("--json", action="store_true", help="Structured JSON output")
    p_sum.add_argument("--verbose", action="store_true", help="Full detail")

    # compare
    p_cmp = sub.add_parser("compare", help="Success vs failure diff or two-file diff")
    p_cmp.add_argument("input", nargs="+", help="File(s) or directory")
    p_cmp.add_argument("--json", action="store_true")
    p_cmp.add_argument("--verbose", action="store_true")

    # errors
    p_err = sub.add_parser("errors", help="Group and correlate errors")
    p_err.add_argument("input", help="JSONL/JSON file or directory")
    p_err.add_argument("--group-by", choices=["type", "time", "trace"], default="type")
    p_err.add_argument("--json", action="store_true")
    p_err.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    if args.command == "summary":
        traces = load_input(args.input)
        if not traces:
            print("No traces found.", file=sys.stderr)
            sys.exit(1)
        cmd_summary(traces, args.verbose, args.json)

    elif args.command == "compare":
        cmd_compare(args.input, args.verbose, args.json)

    elif args.command == "errors":
        traces = load_input(args.input)
        if not traces:
            print("No traces found.", file=sys.stderr)
            sys.exit(1)
        cmd_errors(traces, args.group_by, args.verbose, args.json)


if __name__ == "__main__":
    main()
