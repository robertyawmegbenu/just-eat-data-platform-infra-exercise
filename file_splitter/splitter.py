from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FileSplitter:
    input_file: Path
    output_dir: Path
    max_bytes: int
    max_lines: int
    include_header: bool = True
    encoding: str = "utf-8"
    verbose: bool = False

    # internal state
    _out_handle: Optional[object] = None
    _part_index: int = 0
    _current_bytes: int = 0
    _current_lines: int = 0
    _base_stem: str = ""
    _ext: str = ""
    _header: str = ""
    _has_header: bool = False

    def split(self) -> int:
        self._validate_inputs()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._base_stem, self._ext = self._stem_and_ext(self.input_file.name)

        with self.input_file.open("r", encoding=self.encoding, newline="") as inp:
            first_line = inp.readline()
            self._has_header = self._looks_like_header(first_line)
            self._header = first_line if self._has_header else ""

            header_bytes = len(self._header.encode(self.encoding)) if self._header else 0
            if self._has_header and self.include_header:
                if header_bytes > self.max_bytes:
                    raise ValueError("Header alone exceeds --max-bytes; cannot create compliant output.")
                if self.max_lines < 1:
                    raise ValueError("--max-lines is less than 1 but a header must occupy at least one line.")

            self._open_new_part()

            # If the first line is actually data (no header), write it
            if not self._has_header and first_line:
                self._write_line_with_rotation(first_line)

            # Process remaining lines
            for line in inp:
                if line:
                    self._write_line_with_rotation(line)

        self._close_part(remove_if_empty=True)
        return self._part_index

    # ---- internals ----

    def _validate_inputs(self):
        if not self.input_file.exists() or not self.input_file.is_file():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        if self.max_bytes <= 0:
            raise ValueError("--max-bytes must be a positive integer.")
        if self.max_lines <= 0:
            raise ValueError("--max-lines must be a positive integer.")

    @staticmethod
    def _stem_and_ext(filename: str) -> tuple[str, str]:
        p = Path(filename)
        return (p.stem, p.suffix if p.suffix else "")

    @staticmethod
    def _looks_like_header(first_line: str) -> bool:
        if not first_line:
            return False
        stripped = first_line.strip()
        if "," not in stripped:
            return False
        first_field = stripped.split(",", 1)[0]
        return not first_field.strip().isdigit()

    def _open_new_part(self):
        self._close_part(remove_if_empty=True)
        out_path = self.output_dir / f"{self._base_stem}-part{self._part_index}{self._ext}"
        self._part_index += 1
        self._out_handle = out_path.open("w", encoding=self.encoding, newline="\n")
        self._current_bytes = 0
        self._current_lines = 0
        if self.verbose:
            print(f"Opened {out_path}")

        if self._has_header and self.include_header:
            self._assert_can_fit_line(self._header)
            self._out_handle.write(self._header)
            self._current_bytes += len(self._header.encode(self.encoding))
            self._current_lines += 1

    def _close_part(self, remove_if_empty: bool = False):
        if self._out_handle is None:
            return
        self._out_handle.flush()
        self._out_handle.close()
        last_path = self.output_dir / f"{self._base_stem}-part{self._part_index - 1}{self._ext}"
        if remove_if_empty and last_path.exists() and last_path.stat().st_size == 0:
            last_path.unlink()
            self._part_index -= 1
        self._out_handle = None

    def _assert_can_fit_line(self, line: str):
        line_bytes = len(line.encode(self.encoding))
        if line_bytes > self.max_bytes:
            raise ValueError(
                "A single line (record) exceeds --max-bytes; cannot create compliant output. "
                "Increase --max-bytes or pre-process very long rows."
            )

    def _write_line_with_rotation(self, line: str):
        self._assert_can_fit_line(line)
        line_bytes = len(line.encode(self.encoding))

        would_bytes = self._current_bytes + line_bytes
        would_lines = self._current_lines + 1
        if would_bytes > self.max_bytes or would_lines > self.max_lines:
            self._open_new_part()

        # Write line to the (possibly new) part
        assert self._out_handle is not None
        self._out_handle.write(line)
        self._current_bytes += line_bytes
        self._current_lines += 1
