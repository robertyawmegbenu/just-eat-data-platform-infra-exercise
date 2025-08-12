from pathlib import Path
from file_splitter.splitter import FileSplitter


def write_tmp_csv(tmp_path: Path, name: str, lines: list[str]) -> Path:
    p = tmp_path / name
    p.write_text("".join(lines), encoding="utf-8", newline="\n")
    return p



def test_split_by_lines_with_header(tmp_path: Path):
    lines = [
        "id,name\n",
        "1,Alice\n",
        "2,Bob\n",
        "3,Carol\n",
        "4,Dan\n",
    ]
    inp = write_tmp_csv(tmp_path, "data.csv", lines)
    outdir = tmp_path / "out"

    splitter = FileSplitter(
        input_file=inp,
        output_dir=outdir,
        max_bytes=10_000,
        max_lines=3,
        include_header=True,
    )
    parts = splitter.split()
    assert parts == 2

    p0 = outdir / "data-part0.csv"
    p1 = outdir / "data-part1.csv"
    assert p0.exists() and p1.exists()

    # Verify line counts
    assert len(p0.read_text(encoding="utf-8").splitlines()) <= 3
    assert len(p1.read_text(encoding="utf-8").splitlines()) <= 3


def test_split_by_bytes(tmp_path: Path):
    # Each data line is 10 bytes incl. newline approx; set tight byte limit.
    lines = [
        "id,name\n",         # ~8 bytes
        "1,AAAAAAAA\n",      # 12 bytes
        "2,BBBBBBBB\n",      # 12 bytes
        "3,CCCCCCCC\n",      # 12 bytes
    ]
    inp = write_tmp_csv(tmp_path, "big.csv", lines)
    outdir = tmp_path / "out"

    splitter = FileSplitter(
        input_file=inp,
        output_dir=outdir,
        max_bytes=20,
        max_lines=100,
        include_header=True,
    )
    parts = splitter.split()
    assert parts >= 2

    # Verify each file <= max_bytes
    for i in range(parts):
        part = outdir / f"big-part{i}.csv"
        assert part.exists()
        assert part.stat().st_size <= 20
