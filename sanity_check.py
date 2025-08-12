#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class PartCheck:
    path: str
    bytes: int
    lines: int
    bytes_ok: bool
    lines_ok: bool
    header_matches: Optional[bool]  # None if header check not requested


@dataclass
class SanityReport:
    original_file: str
    parts_dir: str
    glob_pattern: str
    max_bytes: int
    max_lines: int
    total_parts: int
    violations: List[PartCheck]
    passed: bool
    # header/recombine extras
    header_checked: bool
    header_mismatches: List[str]
    original_lines: Optional[int]
    recombined_lines_estimate: Optional[int]
    recombined_lines_match: Optional[bool]
    recombined_written_path: Optional[str]


def count_lines(p: Path, encoding="utf-8") -> int:
    # universal-newline read so CRLF/LF are handled
    with p.open("r", encoding=encoding, newline="") as f:
        return sum(1 for _ in f)


def read_first_line(p: Path, encoding="utf-8") -> str:
    with p.open("r", encoding=encoding, newline="") as f:
        return f.readline()


def recombine_to_file(parts: List[Path], out_path: Path, orig_header: str, header_matches: List[bool], encoding="utf-8") -> int:
    """
    Write a recombined file with the header only once.
    Skip the first line of part[i] if header_matches[i] is True.
    Returns number of lines written.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total_written = 0
    with out_path.open("w", encoding=encoding, newline="\n") as out:
        if orig_header:
            out.write(orig_header)
            total_written += 1
        for i, part in enumerate(parts):
            with part.open("r", encoding=encoding, newline="") as fp:
                # skip header line on part>0 if it matches original
                if i == 0:
                    # we already wrote header; skip the first line if it equals original header
                    first = fp.readline()
                    # if the first line didn't equal header (weird), we already wrote orig header, so
                    # keep all lines including first to avoid losing data.
                    if first and first != orig_header:
                        out.write(first)
                        total_written += 1
                else:
                    if header_matches[i]:
                        _ = fp.readline()  # skip replicated header
                for line in fp:
                    out.write(line)
                    total_written += 1
    return total_written


def main():
    ap = argparse.ArgumentParser(
        description="Sanity-check split CSV outputs against size/line limits, "
                    "optionally verify that part headers match the original header, "
                    "and optionally recombine to validate integrity."
    )
    ap.add_argument("--original-file", type=Path, required=True, help="Path to the original CSV (used for header + integrity checks).")
    ap.add_argument("--parts-dir", type=Path, required=True, help="Directory containing split parts.")
    ap.add_argument("--pattern", type=str, default=None, help="Glob for parts. Default: <stem>-part*.csv based on original filename.")
    ap.add_argument("--max-bytes", type=int, required=True, help="Max bytes per part.")
    ap.add_argument("--max-lines", type=int, required=True, help="Max lines per part.")
    ap.add_argument("--output-dir", type=Path, default=Path("sanity_checks"), help="Folder for reports and (optional) recombined file.")
    ap.add_argument("--encoding", default="utf-8", help="Text encoding (default: utf-8).")
    ap.add_argument("--check-headers", action="store_true", help="Verify that each part's first line equals the original header.")
    ap.add_argument("--recombine", action="store_true", help="Verify integrity by estimating recombined line count (no file written).")
    ap.add_argument("--write-recombined", action="store_true", help="Write a recombined CSV with header only once (can be very large).")

    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.original_file.exists():
        raise SystemExit(f"Original file not found: {args.original_file}")
    if not args.parts_dir.exists():
        raise SystemExit(f"Parts directory not found: {args.parts_dir}")

    # Determine default pattern from original filename if not provided
    stem = args.original_file.stem
    pattern = args.pattern or f"{stem}-part*.csv"

    parts = sorted(args.parts_dir.glob(pattern), key=lambda p: int(p.stem.split("part")[-1]) if "part" in p.stem else 0)
    if not parts:
        raise SystemExit(f"No parts matched pattern '{pattern}' in {args.parts_dir}")

    # Read original header + line count
    orig_header = read_first_line(args.original_file, encoding=args.encoding)
    orig_lines = count_lines(args.original_file, encoding=args.encoding)

    # Per-part checks
    results: List[PartCheck] = []
    header_mismatches: List[str] = []
    header_matches_flags: List[bool] = []

    for p in parts:
        b = p.stat().st_size
        n = count_lines(p, encoding=args.encoding)

        header_match: Optional[bool] = None
        if args.check_headers:
            first = read_first_line(p, encoding=args.encoding)
            header_match = (first == orig_header)
            header_matches_flags.append(bool(header_match))
            if not header_match:
                header_mismatches.append(str(p))

        results.append(
            PartCheck(
                path=str(p),
                bytes=b,
                lines=n,
                bytes_ok=(b <= args.max_bytes),
                lines_ok=(n <= args.max_lines),
                header_matches=header_match,
            )
        )

    # If header check not requested, still need flags list for recombine math
    if not args.check_headers:
        # Assume parts contain repeated header (safe default for your splitter)
        header_matches_flags = [True] * len(parts)

    violations = [r for r in results if not (r.bytes_ok and r.lines_ok)]
    passed_limits = len(violations) == 0

    # Recombine integrity (estimate or write file)
    recombined_lines_estimate: Optional[int] = None
    recombined_lines_match: Optional[bool] = None
    recombined_written_path: Optional[str] = None

    if args.recombine or args.write_recombined:
        # Estimate recombined line count by subtracting 1 from parts that repeat header, except first.
        recombined_lines_estimate = 0
        for i, r in enumerate(results):
            if i == 0:
                # If part0 has a header (match True), we count all lines since we'll drop its header
                # only if we separately wrote orig_header at the top; but for the count-only estimate,
                # we mirror the final recombined layout: header once + all data rows.
                # The final recombined file has: 1 header + (part0_lines - 1 if header present else part0_lines)
                if header_matches_flags[i]:
                    recombined_lines_estimate += 1 + max(r.lines - 1, 0)
                else:
                    # if part0 has no header, we still put original header at top, then all of part0
                    recombined_lines_estimate += 1 + r.lines
            else:
                # For subsequent parts, if they have header=match, drop it
                if header_matches_flags[i]:
                    recombined_lines_estimate += max(r.lines - 1, 0)
                else:
                    recombined_lines_estimate += r.lines

        recombined_lines_match = (recombined_lines_estimate == orig_lines)

    if args.write_recombined:
        out_recombined = args.output_dir / "recombined.csv"
        lines_written = recombine_to_file(
            parts=parts,
            out_path=out_recombined,
            orig_header=orig_header,
            header_matches=header_matches_flags,
            encoding=args.encoding,
        )
        recombined_written_path = str(out_recombined)
        # lines_written should equal orig_lines; if not, integrity differs
        if recombined_lines_estimate is not None and lines_written != recombined_lines_estimate:
            # in a rare mismatch (e.g., weird header shape), re-evaluate match vs original
            recombined_lines_estimate = lines_written
        if recombined_lines_estimate is not None:
            recombined_lines_match = (recombined_lines_estimate == orig_lines)

    # Overall pass/fail: limits OK + (if header checked, no mismatches) + (if recombine requested, counts match)
    passed = passed_limits
    if args.check_headers:
        passed = passed and (len(header_mismatches) == 0)
    if args.recombine or args.write_recombined:
        passed = passed and bool(recombined_lines_match)

    report = SanityReport(
        original_file=str(args.original_file),
        parts_dir=str(args.parts_dir),
        glob_pattern=pattern,
        max_bytes=args.max_bytes,
        max_lines=args.max_lines,
        total_parts=len(parts),
        violations=violations,
        passed=passed,
        header_checked=args.check_headers,
        header_mismatches=header_mismatches,
        original_lines=orig_lines,
        recombined_lines_estimate=recombined_lines_estimate,
        recombined_lines_match=recombined_lines_match,
        recombined_written_path=recombined_written_path,
    )

    # Write JSON
    json_path = args.output_dir / "sanity_report.json"
    with json_path.open("w", encoding="utf-8") as jf:
        json.dump(
            {
                **asdict(report),
                "violations": [asdict(v) for v in report.violations],
            },
            jf,
            indent=2,
        )

    # Write human-readable TXT
    txt_path = args.output_dir / "sanity_report.txt"
    with txt_path.open("w", encoding="utf-8", newline="\n") as tf:
        tf.write("# Sanity Check Report\n\n")
        tf.write(f"Original file: {report.original_file}\n")
        tf.write(f"Parts dir:     {report.parts_dir}\n")
        tf.write(f"Pattern:       {report.glob_pattern}\n")
        tf.write(f"Max bytes:     {report.max_bytes}\n")
        tf.write(f"Max lines:     {report.max_lines}\n\n")
        tf.write(f"Total parts:   {report.total_parts}\n")
        tf.write(f"Limits OK:     {'YES' if passed_limits else 'NO'}\n")
        if report.header_checked:
            tf.write(f"Header check:  {'OK' if len(header_mismatches) == 0 else 'MISMATCHES FOUND'}\n")
        if report.original_lines is not None:
            tf.write(f"Original lines: {report.original_lines}\n")
        if report.recombined_lines_estimate is not None:
            tf.write(f"Recombined lines (est.): {report.recombined_lines_estimate}\n")
            tf.write(f"Line count match: {'YES' if report.recombined_lines_match else 'NO'}\n")
        if report.recombined_written_path:
            tf.write(f"Recombined file written: {report.recombined_written_path}\n")
        tf.write(f"\nPASSED (all checks): {report.passed}\n\n")
        if violations:
            tf.write("Violations (limit failures):\n")
            for v in violations:
                tf.write(
                    f"- {v.path} :: {v.bytes} bytes ({'OK' if v.bytes_ok else 'Too big'}), "
                    f"{v.lines} lines ({'OK' if v.lines_ok else 'Too many'})\n"
                )
        if report.header_checked and header_mismatches:
            tf.write("\nHeader mismatches:\n")
            for p in header_mismatches:
                tf.write(f"- {p}\n")

    print(f"✔ Wrote: {json_path}")
    print(f"✔ Wrote: {txt_path}")
    if report.recombined_written_path:
        print(f"✔ Wrote: {report.recombined_written_path}")
    if not report.passed:
        print("⚠ Sanity checks FAILED. See report files for details.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
