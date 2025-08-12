# CSV File Splitter & Sanity Checker

## Overview

This project was developed as part of a **Data Engineer recruitment coding exercise** for **Just Eat**.
It provides a **command-line application** capable of:

1. Splitting a large CSV file into multiple smaller files without exceeding specified maximum file size (in bytes) and maximum number of lines.
2. Validating the generated parts against these constraints to ensure data integrity.
3. Optionally recombining the split files and verifying that they match the original CSV in both structure and record count.

Two large sample datasets are included for testing, **and a small CSV (`test_500_100.csv`) has been added to the repository** for quick verification using the example limits in the brief.

**Important:**
The two large datasets below are provided in compressed (`.zip`) format due to their size.
Before running any scripts, extract them to the **root directory** of this project.

You can extract the datasets into the current directory using the following commands:

```bash
unzip -j chicago_crimes.zip -d .
unzip -j nyc_collisions.zip -d .
```

These commands will:

* **`-j`**: Ignore any folder paths inside the ZIP file and place the contents directly in the current directory.
* **`-d .`**: Specify the current directory (`.`) as the extraction destination.

After running them, you should see `chicago_crimes.csv` and `nyc_collisions.csv` in the same folder as your project files.
The small file `test_500_100.csv` is already checked into the repo (no unzip needed).

---

## Project Structure

```plaintext
.
├── file-splitter.sh           # Bash wrapper to run the file_splitter package
├── file_splitter/             # Python package for splitting CSV files
│   ├── __init__.py
│   ├── __main__.py            # Enables `python -m file_splitter` usage
│   ├── cli.py                 # CLI argument parsing
│   └── splitter.py            # Core CSV splitting logic
├── sanity_check.py            # Validates split files and generates reports
├── sanity_checks/             # Output folder for JSON and TXT reports
├── tests/
│   └── test_splitter.py       # Pytest-based unit tests for splitter logic
├── test_500_100.csv           # Small demo CSV (example-limits friendly)
├── chicago_crimes.csv         # Sample dataset 1 (unzipped after extract)
├── nyc_collisions.csv         # Sample dataset 2 (unzipped after extract)
```

---

## Features

### 1. CSV Splitting

* Preserves headers in each output file.
* Enforces both maximum size (bytes) and maximum lines per file.
* Flexible CLI with required parameters.

### 2. Sanity Checks

* Verifies maximum bytes and maximum lines constraints for each file part.

* Confirms that headers match between the original file and all split parts.

* Recombines all split parts into a single CSV and checks:

  * Total line count matches the original.
  * Only one header row is present in the recombined file.

* Generates both JSON and human-readable TXT reports.

### 3. Testing

* Includes a `pytest` suite to ensure the splitter logic works as intended.
* Tests cover:

  * File naming sequence
  * Header preservation
  * File size and line limits

---

## Running the Tests

Before processing large datasets, run the test suite to verify functionality:

```bash
pytest -vvv tests/test_splitter.py
```

If all tests pass, you may proceed with splitting and validating real data.

---

## Usage

### Step 1 — Split a CSV File

#### Option A (Quick demo using the small file & example limits)

Use the small CSV that fits the problem statement’s example limits:

```bash
rm -rf out_small && mkdir -p out_small

./file-splitter.sh \
  --input-file test_500_100.csv \
  --output-dir out_small \
  --max-bytes 500 \
  --max-lines 100
```

Or directly with Python:

```bash
python -m file_splitter \
  --input-file test_500_100.csv \
  --output-dir out_small \
  --max-bytes 500 \
  --max-lines 100
```

**Example output:**

```
out_small/test_500_100-part0.csv
out_small/test_500_100-part1.csv
...
```

#### Option B (Large dataset demo)

Using `nyc_collisions.csv` with practical limits for a big file:

```bash
./file-splitter.sh \
  --input-file nyc_collisions.csv \
  --output-dir out_collisions \
  --max-bytes 2000000 \
  --max-lines 50000
```

Or directly with Python:

```bash
python -m file_splitter \
  --input-file nyc_collisions.csv \
  --output-dir out_collisions \
  --max-bytes 2000000 \
  --max-lines 50000
```

**Example output:**

```
out_collisions/nyc_collisions-part0.csv
out_collisions/nyc_collisions-part1.csv
...
```

---

### Step 2 — Run Sanity Checks

#### Option A (Small file)

```bash
python sanity_check.py \
  --original-file test_500_100.csv \
  --parts-dir out_small \
  --max-bytes 500 \
  --max-lines 100 \
  --check-headers \
  --recombine
```

#### Option B (Large dataset)

```bash
python sanity_check.py \
  --original-file nyc_collisions.csv \
  --parts-dir out_collisions \
  --max-bytes 2000000 \
  --max-lines 50000 \
  --check-headers \
  --recombine
```

These will:

* Validate all parts against size and line limits.
* Ensure headers match across all files.
* Recombine the files and compare them to the original.
* Save reports to `sanity_checks/`:

```
sanity_checks/sanity_report.json
sanity_checks/sanity_report.txt
```

---

## Sample Sanity Report (TXT)

```
# Sanity Check Report

Original file: nyc_collisions.csv
Parts dir:     out_collisions
Pattern:       nyc_collisions-part*.csv
Max bytes:     2000000
Max lines:     50000

Total parts:   63
Limits OK:     YES
Header check:  OK
Original lines: 1114507
Recombined lines (est.): 1114507
Line count match: YES

PASSED (all checks): True
```

---

## Notes

* The provided datasets are sufficiently large to test splitting at scale.
* A **small CSV (`test_500_100.csv`) is included** to quickly demonstrate the example limits from the problem statement (`--max-bytes 500 --max-lines 100`).
* You can intentionally corrupt files (e.g., change headers or add extra rows) to test failure scenarios in `sanity_check.py`.
* All scripts are cross-platform and require Python 3.8 or later.

---

## Example Workflow

```bash
# 1. Run tests
pytest -vvv

# 2a. Quick demo (small file)
rm -rf out_small && mkdir -p out_small
./file-splitter.sh \
  --input-file test_500_100.csv \
  --output-dir out_small \
  --max-bytes 500 \
  --max-lines 100
python sanity_check.py \
  --original-file test_500_100.csv \
  --parts-dir out_small \
  --max-bytes 500 \
  --max-lines 100 \
  --check-headers \
  --recombine

# 2b. Large demo (nyc collisions)
./file-splitter.sh \
  --input-file nyc_collisions.csv \
  --output-dir out_collisions \
  --max-bytes 2000000 \
  --max-lines 50000
python sanity_check.py \
  --original-file nyc_collisions.csv \
  --parts-dir out_collisions \
  --max-bytes 2000000 \
  --max-lines 50000 \
  --check-headers \
  --recombine
```
