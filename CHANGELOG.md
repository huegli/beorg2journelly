# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-02

### Added
- Initial implementation of beorg2journelly.py script
- 2-way synchronization between BeOrg inbox.org and Journelly.org files
- Command-line interface with support for file path arguments
- Verbose mode (-v/--verbose) for detailed synchronization logging
- Automatic parsing of BeOrg format (* TODO/DONE with timestamps)
- Automatic parsing of Journelly format (* timestamp with - [ ]/- [X] tasks)
- Conflict resolution using earlier timestamps when same task exists in both files
- Automatic removal of completed tasks from both files
- Automatic addition of incomplete tasks to both files when found in only one
- Proper handling of ignored headers (non-TODO/DONE in BeOrg, non-task lines in Journelly)
- Comprehensive error handling and user-friendly error messages
- Python 3.12+ compatibility with no external dependencies
- Flake8 compliant code formatting
- Test data files with various scenarios for validation
- Complete documentation in CLAUDE.md

### Technical Details
- Uses Python's built-in libraries only (argparse, re, datetime, sys, typing)
- Implements three main classes: BeOrgParser, JournellyParser, TaskSynchronizer
- Task matching by exact text content
- Preserves file formats while synchronizing content
- Idempotent operation - multiple runs produce same result