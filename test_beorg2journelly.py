import unittest
from datetime import datetime

# Assuming the classes are in beorg2journelly.py in the same directory
from beorg2journelly import (
    Task, BeOrgParser, JournellyParser, TaskSynchronizer
)


class TestParsersWithExtendedCases(unittest.TestCase):
    def setUp(self):
        """Set up 8 diverse tasks for comprehensive testing."""
        self.tasks = [
            Task("Simple incomplete", datetime(2024, 1, 1, 10, 0), False),
            Task("Simple completed", datetime(2024, 1, 2, 11, 0), True),
            Task("Task with numbers 123", datetime(2024, 2, 5, 15, 30), False),
            Task("Task with symbols !@#$%^&*()", datetime(2024, 2, 10, 9, 0),
                 True),
            Task("Another incomplete task", datetime(2024, 3, 1, 12, 0),
                 False),
            Task("A task to be done soon", datetime(2024, 3, 15, 18, 45),
                 False),
            Task("This is a very long task description to see how it is handled",
                 datetime(2024, 4, 1, 8, 0), False),
            Task("Final task for this test suite",
                 datetime(2024, 4, 20, 20, 20), False),
        ]
        self.beorg_parser = BeOrgParser()
        self.journelly_parser = JournellyParser()

    def test_beorg_parser_parse(self):
        """Test BeOrg parser with 8 tasks and extra non-task content."""
        content = """
* Some other header
* TODO Simple incomplete
[2024-01-01 Mon 10:00]

* DONE Simple completed
[2024-01-02 Tue 11:00]
* TODO Task with numbers 123
[2024-02-05 Mon 15:30]
* DONE Task with symbols !@#$%^&*()
[2024-02-10 Sat 09:00]
* A random line that should be ignored
* TODO Another incomplete task
[2024-03-01 Fri 12:00]
* TODO A task to be done soon
[2024-03-15 Fri 18:45]
* TODO This is a very long task description to see how it is handled
[2024-04-01 Mon 08:00]
* TODO Final task for this test suite
[2024-04-20 Sat 20:20]
        """
        parsed_tasks = self.beorg_parser._parse_tasks(content)
        self.assertEqual(parsed_tasks, self.tasks)

    def test_beorg_parser_format(self):
        """Test BeOrg formatter with 8 tasks."""
        expected_lines = [
            "* TODO Simple incomplete", "[2024-01-01 Mon 10:00]",
            "* DONE Simple completed", "[2024-01-02 Tue 11:00]",
            "* TODO Task with numbers 123", "[2024-02-05 Mon 15:30]",
            "* DONE Task with symbols !@#$%^&*()", "[2024-02-10 Sat 09:00]",
            "* TODO Another incomplete task", "[2024-03-01 Fri 12:00]",
            "* TODO A task to be done soon", "[2024-03-15 Fri 18:45]",
            "* TODO This is a very long task description to see how it is handled",
            "[2024-04-01 Mon 08:00]",
            "* TODO Final task for this test suite", "[2024-04-20 Sat 20:20]",
        ]
        formatted_lines = self.beorg_parser._format_tasks(self.tasks)
        self.assertEqual(formatted_lines, expected_lines)

    def test_journelly_parser_parse(self):
        """Test Journelly parser with 8 tasks and extra non-task content."""
        content = """
* [2024-01-01 Mon 10:00] @ -
- [ ] Simple incomplete
* Some other header
* [2024-01-02 Tue 11:00] @ -
- [X] Simple completed

* [2024-02-05 Mon 15:30] @ -
- [ ] Task with numbers 123
* [2024-02-10 Sat 09:00] @ -
- [X] Task with symbols !@#$%^&*()
* [2024-03-01 Fri 12:00] @ -
- [ ] Another incomplete task
* [2024-03-15 Fri 18:45] @ -
- [ ] A task to be done soon
* A random line to be ignored
* [2024-04-01 Mon 08:00] @ -
- [ ] This is a very long task description to see how it is handled
* [2024-04-20 Sat 20:20] @ -
- [ ] Final task for this test suite
        """
        parsed_tasks = self.journelly_parser._parse_tasks(content)
        self.assertEqual(parsed_tasks, self.tasks)

    def test_journelly_parser_format(self):
        """Test Journelly formatter with 8 tasks."""
        expected_lines = [
            "* [2024-01-01 Mon 10:00] @ -", "- [ ] Simple incomplete",
            "* [2024-01-02 Tue 11:00] @ -", "- [X] Simple completed",
            "* [2024-02-05 Mon 15:30] @ -", "- [ ] Task with numbers 123",
            "* [2024-02-10 Sat 09:00] @ -", "- [X] Task with symbols !@#$%^&*()",
            "* [2024-03-01 Fri 12:00] @ -", "- [ ] Another incomplete task",
            "* [2024-03-15 Fri 18:45] @ -", "- [ ] A task to be done soon",
            "* [2024-04-01 Mon 08:00] @ -",
            "- [ ] This is a very long task description to see how it is handled",
            "* [2024-04-20 Sat 20:20] @ -",
            "- [ ] Final task for this test suite",
        ]
        formatted_lines = self.journelly_parser._format_tasks(self.tasks)
        self.assertEqual(formatted_lines, expected_lines)


class TestTaskSynchronizer(unittest.TestCase):
    def setUp(self):
        self.synchronizer = TaskSynchronizer()
        self.task_a = Task("Task A", datetime(2023, 1, 1), False)
        self.task_b = Task("Task B", datetime(2023, 1, 2), False)
        self.task_c_done = Task("Task C", datetime(2023, 1, 3), True)
        self.task_d_early = Task("Task D", datetime(2023, 1, 4), False)
        self.task_d_late = Task("Task D", datetime(2023, 1, 5), False)

    def test_sync_new_from_beorg(self):
        """New incomplete task in BeOrg should be added to Journelly."""
        beorg = [self.task_a]
        journelly = []
        synced_b, synced_j = self.synchronizer.synchronize(beorg, journelly)
        self.assertEqual(synced_b, [self.task_a])
        self.assertEqual(synced_j, [self.task_a])

    def test_sync_new_from_journelly(self):
        """New incomplete task in Journelly should be added to BeOrg."""
        beorg = []
        journelly = [self.task_b]
        synced_b, synced_j = self.synchronizer.synchronize(beorg, journelly)
        self.assertEqual(synced_b, [self.task_b])
        self.assertEqual(synced_j, [self.task_b])

    def test_sync_completed_task_removed(self):
        """Completed task should be removed from both."""
        beorg = [self.task_a, self.task_c_done]
        journelly = [self.task_a]
        synced_b, synced_j = self.synchronizer.synchronize(beorg, journelly)
        self.assertEqual(synced_b, [self.task_a])
        self.assertEqual(synced_j, [self.task_a])

    def test_sync_task_completed_in_one_file(self):
        """Task marked done in one file is removed from both."""
        task_a_done = self.task_a._replace(is_completed=True)
        beorg = [self.task_a]
        journelly = [task_a_done]
        synced_b, synced_j = self.synchronizer.synchronize(beorg, journelly)
        self.assertEqual(synced_b, [])
        self.assertEqual(synced_j, [])

    def test_sync_timestamp_conflict(self):
        """Earlier timestamp should be preserved."""
        beorg = [self.task_d_late]
        journelly = [self.task_d_early]
        synced_b, synced_j = self.synchronizer.synchronize(beorg, journelly)
        self.assertEqual(synced_b, [self.task_d_early])
        self.assertEqual(synced_j, [self.task_d_early])


if __name__ == '__main__':
    unittest.main()
