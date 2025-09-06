"""
beorg2journelly.py - 2-way sync tool between BeOrg and Journelly files

This script synchronizes TODO tasks between a BeOrg inbox.org file and
a Journelly.org file.
- Incomplete tasks appearing in only one file are added to the other
- Completed tasks are removed from both files
- Tasks are matched by exact text content
- Earlier timestamps are preserved on conflicts
"""

import argparse
import re
import sys
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional, Set, Tuple, override
import abc


class Task(NamedTuple):
    """Represents a TODO task with content, timestamp, and completion."""
    content: str
    timestamp: datetime
    is_completed: bool


class SyncError(Exception):
    """Base exception for synchronization errors."""
    pass


class FileIOError(SyncError):
    """Exception for file input/output errors."""
    pass


class BaseParser(abc.ABC):
    """Abstract base class for task parsers."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.warnings: List[str] = []

    def _create_task_and_log(self, task_content: str, timestamp: datetime,
                             is_completed: bool, timestamp_str: str,
                             parser_name: str) -> Task:
        """Creates a Task object and logs it if verbose mode is on."""
        task = Task(task_content, timestamp, is_completed)
        if self.verbose:
            status = "DONE" if is_completed else "TODO"
            msg = (f"Parsed {parser_name} task: [{status}] "
                   f"{task_content} at {timestamp_str}")
            print(msg)
        return task

    def parse_file(self, filepath: str) -> List[Task]:
        """Read a file and parse tasks from its content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            if self.verbose:
                parser_name = self.__class__.__name__.replace('Parser', '')
                print(f"{parser_name} file not found: {filepath}, "
                      f"treating as empty")
            return []
        except IOError as e:
            raise FileIOError(f"Error reading file {filepath}: {e}") from e
        return self._parse_tasks(content)

    @abc.abstractmethod
    def _parse_tasks(self, content: str) -> List[Task]:
        """Parse tasks from a string of file content."""
        raise NotImplementedError

    def write_file(self, filepath: str, tasks: List[Task]) -> None:
        """Format and write tasks to a file, sorted by timestamp."""
        sorted_tasks = sorted(tasks, key=lambda t: t.timestamp, reverse=True)
        lines = self._format_tasks(sorted_tasks)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
                if lines:
                    f.write('\n')
        except IOError as e:
            raise FileIOError(f"Error writing to file {filepath}: {e}") from e

    @abc.abstractmethod
    def _format_tasks(self, tasks: List[Task]) -> List[str]:
        """Format tasks into a list of strings for file writing."""
        raise NotImplementedError


class BeOrgParser(BaseParser):
    """Parser for BeOrg inbox.org file format."""

    @override
    def _parse_tasks(self, content: str) -> List[Task]:
        """Parse tasks from BeOrg file content."""
        tasks = []
        lines = content.strip().split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Look for level 1 headers starting with TODO or DONE
            task, lines_consumed = self._parse_task_from_line(line, lines, i)
            if task:
                tasks.append(task)
            i += 1 + lines_consumed

        return tasks

    def _parse_task_from_line(self, line: str, lines: List[str], i: int
                              ) -> Tuple[Optional[Task], int]:
        """Parses a single task starting from a given line if it's a header."""
        if not (line.startswith('* TODO ') or line.startswith('* DONE ')):
            return None, 0

        is_completed = line.startswith('* DONE ')
        task_content = line[7:]  # Remove "* TODO " or "* DONE "

        return self._parse_beorg_timestamp_and_create_task(
            task_content, is_completed, lines, i, line)

    def _parse_beorg_timestamp_and_create_task(
            self, task_content: str, is_completed: bool, lines: List[str],
            i: int, header_line: str) -> Tuple[Optional[Task], int]:
        """Parses timestamp for a BeOrg task and returns the Task object."""
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            pattern = r'\[(\d{4}-\d{2}-\d{2} \w{3} \d{2}:\d{2})\]'
            timestamp_match = re.match(pattern, next_line)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                try:
                    timestamp = datetime.strptime(
                        timestamp_str, '%Y-%m-%d %a %H:%M')
                    task = self._create_task_and_log(
                        task_content, timestamp, is_completed, timestamp_str,
                        "BeOrg")
                    return task, 1  # Consumed 1 extra line for timestamp
                except ValueError:
                    msg = (f"Skipping entry in BeOrg file due to invalid "
                           f"timestamp: '{timestamp_str}'")
                    self.warnings.append(msg)
            else:
                msg = (f"Skipping malformed BeOrg task (timestamp "
                       f"missing or wrong format): '{header_line}'")
                self.warnings.append(msg)
        else:
            msg = (f"Skipping BeOrg task at end of file (timestamp "
                   f"missing): '{header_line}'")
            self.warnings.append(msg)

        return None, 0

    @override
    def _format_tasks(self, tasks: List[Task]) -> List[str]:
        """Formats tasks into BeOrg format."""
        lines = []
        for task in tasks:
            status = "DONE" if task.is_completed else "TODO"
            lines.append(f"* {status} {task.content}")
            timestamp_str = task.timestamp.strftime('%Y-%m-%d %a %H:%M')
            lines.append(f"[{timestamp_str}]")
        return lines


class JournellyParser(BaseParser):
    """Parser for Journelly.org file format."""

    @override
    def _parse_tasks(self, content: str) -> List[Task]:
        """Parse tasks from Journelly file content."""
        tasks = []
        lines = content.strip().split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            task, lines_consumed = self._parse_journelly_task_from_line(
                line, lines, i)
            if task:
                tasks.append(task)
            i += 1 + lines_consumed

        return tasks

    def _parse_journelly_task_from_line(self, line: str, lines: List[str],
                                        i: int) -> Tuple[Optional[Task], int]:
        """Parses a Journelly task if the line is a timestamp header."""
        pattern = r'\* \[(\d{4}-\d{2}-\d{2} \w{3} \d{2}:\d{2})\] @ -'
        timestamp_match = re.match(pattern, line)
        if not timestamp_match:
            return None, 0

        timestamp_str = timestamp_match.group(1)
        try:
            timestamp = datetime.strptime(
                timestamp_str, '%Y-%m-%d %a %H:%M')

            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith(('- [ ] ', '- [X] ')):
                    is_completed = next_line.startswith('- [X] ')
                    task_content = next_line[6:]
                    task = self._create_task_and_log(
                        task_content, timestamp, is_completed, timestamp_str,
                        "Journelly")
                    return task, 1  # Consumed 1 extra line for timestamp
                else:
                    msg = (f"Skipping malformed Journelly entry (task line "
                           f"missing after timestamp): '{line}'")
                    self.warnings.append(msg)
            else:
                msg = (f"Skipping malformed Journelly entry (task line "
                       f"missing at end of file): '{line}'")
                self.warnings.append(msg)
        except ValueError:
            msg = (f"Skipping entry in Journelly file due to "
                   f"invalid timestamp: '{timestamp_str}'")
            self.warnings.append(msg)

        return None, 0

    @override
    def _format_tasks(self, tasks: List[Task]) -> List[str]:
        """Formats tasks into Journelly format."""
        lines = []
        for task in tasks:
            timestamp_str = task.timestamp.strftime('%Y-%m-%d %a %H:%M')
            lines.append(f"* [{timestamp_str}] @ -")
            status = "[X]" if task.is_completed else "[ ]"
            lines.append(f"- {status} {task.content}")
        return lines


class TaskSynchronizer:
    """Handles 2-way synchronization between BeOrg and Journelly tasks."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def synchronize(self, beorg_tasks: List[Task],
                    journelly_tasks: List[Task]) -> Tuple[
                        List[Task], List[Task]]:
        """
        Synchronize tasks between BeOrg and Journelly formats.
        Returns tuple of (beorg_tasks, journelly_tasks).
        """
        # Create lookup dictionaries by task content
        beorg_by_content: Dict[str, Task] = {
            task.content: task for task in beorg_tasks}
        journelly_by_content: Dict[str, Task] = {
            task.content: task for task in journelly_tasks}

        # Find all unique task contents
        all_contents: Set[str] = (
            set(beorg_by_content.keys()) | set(journelly_by_content.keys()))

        final_beorg_tasks = []
        final_journelly_tasks = []

        for content in all_contents:
            beorg_task = beorg_by_content.get(content)
            journelly_task = journelly_by_content.get(content)

            if beorg_task and journelly_task:
                # Task exists in both files, refactor this into a separate function, AI!
                if self.verbose:
                    print(f"Task exists in both files: {content}")

                # Use earlier timestamp (conflict resolution)
                earlier_timestamp = min(beorg_task.timestamp,
                                        journelly_task.timestamp)

                # Determine completion status
                is_completed = (
                    beorg_task.is_completed or journelly_task.is_completed)

                merged_task = Task(content, earlier_timestamp, is_completed)

                if is_completed:
                    # Remove completed tasks from both files
                    if self.verbose:
                        msg = (f"Removing completed task from both files: "
                               f"{content}")
                        print(msg)
                else:
                    # Keep incomplete tasks in both files
                    final_beorg_tasks.append(merged_task)
                    final_journelly_tasks.append(merged_task)
                    if self.verbose:
                        msg = (f"Keeping incomplete task in both files: "
                               f"{content}")
                        print(msg)

            elif beorg_task or journelly_task:
                # Task exists in one file only, refactor this into a separate function AI!
                single_task = beorg_task or journelly_task
                source = "BeOrg" if beorg_task else "Journelly"
                if self.verbose:
                    print(f"Task exists only in {source}: {content}")

                if single_task.is_completed:
                    # Remove completed task by not adding it to final lists
                    if self.verbose:
                        msg = (f"Removing completed task from {source}: "
                               f"{content}")
                        print(msg)
                else:
                    # Add incomplete task to both files' final lists
                    final_beorg_tasks.append(single_task)
                    final_journelly_tasks.append(single_task)
                    if self.verbose:
                        dest = "Journelly" if source == "BeOrg" else "BeOrg"
                        msg = (f"Adding incomplete task to {dest}: "
                               f"{content}")
                        print(msg)

        return final_beorg_tasks, final_journelly_tasks


def main():
    """Main entry point for the synchronization script."""
    parser = argparse.ArgumentParser(
        description=('Synchronize TODO tasks between BeOrg inbox.org '
                     'and Journelly.org files'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s beorg_inbox.org journelly.org
  %(prog)s -v ~/Documents/inbox.org ~/Documents/journelly.org
        """
    )

    parser.add_argument('beorg_file', help='Path to BeOrg inbox.org file')
    parser.add_argument('journelly_file', help='Path to Journelly.org file')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output showing details')

    args = parser.parse_args()

    if not args.beorg_file or not args.journelly_file:
        parser.error("Both BeOrg and Journelly file paths are required")
        return 1

    if args.verbose:
        print("Starting synchronization between:")
        print(f"  BeOrg file: {args.beorg_file}")
        print(f"  Journelly file: {args.journelly_file}")
        print()

    try:
        # Parse both files
        beorg_parser = BeOrgParser(args.verbose)
        journelly_parser = JournellyParser(args.verbose)

        beorg_tasks = beorg_parser.parse_file(args.beorg_file)
        journelly_tasks = journelly_parser.parse_file(args.journelly_file)

        # Report any non-fatal parsing warnings
        all_warnings = beorg_parser.warnings + journelly_parser.warnings
        if all_warnings:
            print("\nWarnings encountered during parsing:", file=sys.stderr)
            for warning in all_warnings:
                print(f"- {warning}", file=sys.stderr)

        if args.verbose:
            print(f"\nParsed {len(beorg_tasks)} tasks from BeOrg file")
            print(f"Parsed {len(journelly_tasks)} tasks from Journelly file")
            print("\nStarting synchronization...")
            print()

        # Synchronize tasks
        synchronizer = TaskSynchronizer(args.verbose)
        synced_beorg, synced_journelly = synchronizer.synchronize(
            beorg_tasks, journelly_tasks)

        # Write synchronized tasks back to files
        beorg_parser.write_file(args.beorg_file, synced_beorg)
        journelly_parser.write_file(args.journelly_file, synced_journelly)

        if args.verbose:
            print("\nSynchronization complete!")
            print(f"Final BeOrg tasks: {len(synced_beorg)}")
            print(f"Final Journelly tasks: {len(synced_journelly)}")
        else:
            print("Synchronization complete")

    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
