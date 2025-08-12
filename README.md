# CSV File Splitter & Sanity Checker

## Overview

This project was developed as part of a **Data Engineer recruitment coding exercise** for **Just Eat**.  
It provides a **command-line application** capable of:

1. Splitting a large CSV file into multiple smaller files without exceeding specified maximum file size (in bytes) and maximum number of lines.
2. Validating the generated parts against these constraints to ensure data integrity.
3. Optionally recombining the split files and verifying that they match the original CSV in both structure and record count.

Two sample datasets are included for testing.

**Important:**  
The datasets listed below are provided in compressed (`.zip`) format due to their large size.  
Before running any scripts, extract them to the **root directory** of this project.

- `chicago_crimes.csv` (approximately 900 MB)
- `nyc_collisions.csv` (approximately 125 MB)

---

## Project Structure

```plaintext
.
├── file-splitter.sh           # Bash wrapper to run the file_splitter package
├── file_splitter/              # Python package for splitting CSV files
│   ├── __init__.py
│   ├── __main__.py             # Enables `python -m file_splitter` usage
│   ├── cli.py                  # CLI argument parsing
│   └── splitter.py             # Core CSV splitting logic
├── sanity_check.py             # Validates split files and generates reports
├── sanity_checks/              # Output folder for JSON and TXT reports
├── tests/
│   └── test_splitter.py        # Pytest-based unit tests for splitter logic
├── chicago_crimes.csv          # Sample dataset 1 (unzipped)
├── nyc_collisions.csv          # Sample dataset 2 (unzipped)
```

---

## Features

### 1. CSV Splitting

- Preserves headers in each output file.
- Enforces both maximum size (bytes) and maximum lines per file.
- Flexible CLI with required parameters.

### 2. Sanity Checks

- Verifies maximum bytes and maximum lines constraints for each file part.
- Confirms that headers match between the original file and all split parts.
- Recombines all split parts into a single CSV and checks:

  - Total line count matches the original.
  - Only one header row is present in the recombined file.

- Generates both JSON and human-readable TXT reports.

### 3. Testing

- Includes a `pytest` suite to ensure the splitter logic works as intended.
- Tests cover:

  - File naming sequence
  - Header preservation
  - File size and line limits

---

## Running the Tests

Before processing large datasets, run the test suite to verify functionality:

```bash
pytest -vvv
```

If all tests pass, you may proceed with splitting and validating real data.

---

## Usage

### Step 1 — Split a CSV File

Using the Bash Script:

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

After splitting:

```bash
python sanity_check.py \
  --original-file nyc_collisions.csv \
  --parts-dir out_collisions \
  --max-bytes 2000000 \
  --max-lines 50000 \
  --check-headers \
  --recombine
```

This will:

- Validate all parts against size and line limits.
- Ensure headers match across all files.
- Recombine the files and compare them to the original.
- Save reports to `sanity_checks/`:

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

- The provided datasets are sufficiently large to test splitting at scale.
- You can intentionally corrupt files (e.g., change headers or add extra rows) to test failure scenarios in `sanity_check.py`.
- All scripts are cross-platform and require Python 3.8 or later.

---

## Example Workflow

```bash
# 1. Run tests
pytest -vvv

# 2. Split chicago_crimes.csv
./file-splitter.sh \
  --input-file chicago_crimes.csv \
  --output-dir out_crimes \
  --max-bytes 2000000 \
  --max-lines 50000

# 3. Validate results
python sanity_check.py \
  --original-file chicago_crimes.csv \
  --parts-dir out_crimes \
  --max-bytes 2000000 \
  --max-lines 50000 \
  --check-headers \
  --recombine
```
