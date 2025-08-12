import argparse
from pathlib import Path
from .splitter import FileSplitter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-splitter",
        description="Split a large CSV file into multiple smaller CSV parts by size and/or line limits.",
    )
    parser.add_argument("--input-file", type=Path, required=True, help="Path to input CSV file.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to write output parts.")
    parser.add_argument("--max-bytes", type=int, required=True, help="Maximum bytes per output file.")
    parser.add_argument("--max-lines", type=int, required=True, help="Maximum lines per output file.")
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Do not repeat the header line in each part. By default, header is repeated if detected.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding for input/output files (default: utf-8).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    splitter = FileSplitter(
        input_file=args.input_file,
        output_dir=args.output_dir,
        max_bytes=args.max_bytes,
        max_lines=args.max_lines,
        include_header=not args.no_header,
        encoding=args.encoding,
        verbose=args.verbose,
    )

    parts = splitter.split()
    if args.verbose:
        print(f"Completed. Wrote {parts} part(s).")