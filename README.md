````markdown
# CSV File Splitter & Sanity Checker

## Overview

This project was implemented as part of a **Data Engineer recruitment coding exercise** for **Just Eat**.  
The task was to design and implement a **command-line application** that:

1. **Splits a large CSV file** into multiple smaller files without exceeding specified **maximum size** and **maximum number of lines**.
2. **Validates** the generated parts against constraints to ensure data integrity.
3. **Optionally recombines** the split files and verifies they match the original CSV in both structure and record count.

Two **sample datasets** are included for testing:

- `chicago_crimes.csv` (~900 MB)
- `nyc_collisions.csv` (~125 MB)

---

## Project Structure

```plaintext
.
├── file-splitter.sh           # Bash wrapper to run the file_splitter package
├── file_splitter/              # Python package for splitting CSV files
│   ├── __init__.py
│   ├── __main__.py             # Allows `python -m file_splitter` usage
│   ├── cli.py                  # CLI argument parsing
│   └── splitter.py             # Core CSV splitting logic
├── sanity_check.py             # Validates split files & generates reports
├── sanity_checks/              # Output folder for JSON & TXT reports
├── tests/
│   └── test_splitter.py        # Pytest-based unit tests for splitter logic
├── chicago_crimes.csv          # Sample dataset 1
├── nyc_collisions.csv          # Sample dataset 2
```
````

---

## Features

### 1. CSV Splitting

- Preserves **headers** in each output part.
- Ensures **max size** (bytes) and **max line** constraints.
- Flexible CLI with required parameters.

### 2. Sanity Checks

- Verifies **max bytes** and **max lines** constraints for each part.
- Compares **headers** between original and all split parts.
- Recombines all split parts into a single CSV and verifies:

  - Total line count matches the original.
  - Only one header row exists in recombined file.

- Produces both **JSON** and **human-readable TXT reports**.

### 3. Testing

- `pytest` test suite to ensure splitter logic works correctly.
- Includes tests for:

  - File naming sequence
  - Header preservation
  - File size & line limits

---

## Running the Tests First

Before running the scripts on sample files, verify functionality using `pytest`:

```bash
pytest -vvv
```

If all tests pass, you are safe to run the splitter and sanity check on real data.

---

## Usage

### 1️. Split a CSV File

Using the Bash wrapper:

```bash
./file-splitter.sh \
  --input-file nyc_collisions.csv \
  --output-dir out_collisions \
  --max-bytes 2000000 \
  --max-lines 50000
```

Or directly via Python:

```bash
python -m file_splitter \
  --input-file nyc_collisions.csv \
  --output-dir out_collisions \
  --max-bytes 2000000 \
  --max-lines 50000
```

**Output example:**

```
out_collisions/nyc_collisions-part0.csv
out_collisions/nyc_collisions-part1.csv
...
```

---

### 2️. Run Sanity Checks

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

**This will:**

- Validate all parts against limits.
- Ensure headers match.
- Recombine parts and compare with the original.
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

- Provided datasets are large enough to properly test **file splitting at scale**.
- You can intentionally corrupt files (e.g., change a header or append extra rows) to test failure cases in `sanity_check.py`.
- All scripts are designed to be **cross-platform** and run on Python 3.8+.

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

---

```

```
