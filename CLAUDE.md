# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains `beorg2journelly.py`, a command-line script that performs a two-way synchronization of TODO tasks between a BeOrg `inbox.org` file and a `Journelly.org` file.

The script ensures that TODO lists remain consistent between the two applications by following these rules:
- Incomplete tasks appearing in only one file are added to the other.
- Completed tasks are removed from both files.
- Tasks are matched by exact text content.
- When the same task exists in both files, the earlier timestamp is preserved.

## Repository Status

The repository contains a functional Python script `beorg2journelly.py` for synchronizing tasks.

## Current State

- **Status**: Active
- **Main Script**: beorg2journelly.py

## File format example for BeOrg inbox.org
```
* TODO This is an incomplete task
[2025-08-31 Sun 11:32]
* DONE This is a completed task
[2025-09-01 Mon 18:10]
```

## File format example for Journelly.org
```
* [2025-08-31 Sun 11:32] @ -
- [ ] This is an incomplete task
* [2025-09-01 Mon 18:10] @ -
- [X] This is a completed task
```

## Requirements
- The script should do 2-way synchronization between a BeOrg inbox.org file and a Journelly.org file
- Script accepts file paths as command-line arguments; outputs helpful error and quits if none provided
- Incomplete tasks that appear only in one of the org file should be added to the other one
- Completed tasks that appear in one or both org files should be removed from both files
- The time-date-stamp for a TODO constitutes the creation date & time
- When same task exists in both files with different timestamps, preserve the earlier timestamp
- Tasks are matched by exact text content
- Level 1 headers that don't start with TODO or DONE (in the BeOrg inbox org file) should be ignored
- Entries in the Journelly org file that don't have a "- [ ]" or "- [X]" in the second line should be ignored
- No backup files are created; direct file modification
- Support `-v` or `--verbose` flag for detailed synchronization logging

## Implentation Architecture

### Code Structure
The script is structured into several classes:
- `Task`: A `NamedTuple` representing a TODO task.
- `BaseParser`: An abstract base class for file parsers, handling common logic like file I/O and task sorting.
- `BeOrgParser` and `JournellyParser`: Concrete implementations of `BaseParser` that handle the specific file formats for BeOrg and Journelly, respectively.
- `TaskSynchronizer`: A class that contains the business logic for synchronizing tasks between the two sources.
- A `main` function handles command-line argument parsing and orchestrates the parsing, synchronization, and writing processes.

### Error Handling
The script uses a custom exception, `FileIOError`, to handle file I/O issues gracefully (e.g., permission errors). This provides clearer feedback than a generic crash.

For parsing, the script adopts a lenient "best effort" approach. When it encounters malformed entries or invalid timestamps, it logs them as warnings and skips them, continuing to process the rest of the file. These warnings are displayed to the user after parsing is complete, ensuring that minor formatting mistakes do not halt the entire synchronization process.

### Tech Stack
- **Python** version 3.12 or later,
- no external library dependencies
- Well documented
- Git Version control

### Linting
- flake8

### Testing
- For testing purpose, create BeOrg inbox.org and Journelly.org files with random TODO entries
- Some of the TODO entries should be incomplete, others should be complete
- Some of the entries should appear in both files, some only in one or the other file
- The test files should also include other level one headers that are to be ignored

### Development flow
- After each change to the beorg2journelly.py, the file should be linted
- If the file is lint clean, create random test data as described and verify the correctness of the beorg2journelly.py synchronization
- If the test synchronization passes, check in the file(s), adding both git comments and an entry into a CHANGELOG.md file

## Improvements
### [X] the TODO entries in both the inbox.org and Journelly.org should be sorted by date, with the latest date first
### [X] Refactored parsers to reduce code duplication by introducing a `BaseParser` abstract class.
### [X] Add unit tests for parsers and synchronizer.
### [X] Improved error handling for malformed file entries and file I/O operations.

### Future Ideas
