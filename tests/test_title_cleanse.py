import importlib.util
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "title_cleanse"
TARGET = "`flickrstats-492309.flickrstats.flickrstats_all`"

spec = importlib.util.spec_from_file_location("title_cleanse", SQL_DIR / "main.py")
cleanse = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanse)


class TitleSelectionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.create_function("STARTS_WITH", 2, lambda text, prefix: text.startswith(prefix))
        self.db.execute(
            "CREATE TABLE stats (`Photo ID` INTEGER, `Photo Title` TEXT, "
            "updated_at TEXT, Link TEXT)"
        )
        self.addCleanup(self.db.close)
        self.query = (SQL_DIR / "select_title_changes.sql").read_text(
            encoding="utf-8"
        ).replace(TARGET, "stats")

    def select(self, rows):
        self.db.executemany("INSERT INTO stats VALUES (?, ?, ?, ?)", rows)
        return {row[0]: (row[1], row[2]) for row in self.db.execute(self.query)}

    def test_selects_latest_valid_title_across_links_and_ignores_camera_names(self):
        rows = [
            (1, "PXL_1", "2026-01-01", "old"),
            (1, "Beach", "2026-01-02", "old"),
            (1, "Sunset", "2026-01-03", "new"),
            (1, "IMG_1", "2026-01-04", "new"),
            (1, None, "2026-01-05", "new"),
        ]
        self.assertEqual(self.select(rows), {1: ("Sunset", "ready")})

    def test_skips_each_camera_prefix_and_missing_timestamps(self):
        rows = [
            (2, "PXL_1", "2026-01-01", ""),
            (2, "IMG_1", "2026-01-02", ""),
            (2, "CR2_1", "2026-01-03", ""),
            (2, "2026 Holiday", "2026-01-04", ""),
            (2, "P100_1", "2026-01-05", ""),
            (2, "Title", None, ""),
        ]
        self.assertEqual(self.select(rows), {2: (None, "no_valid_title")})

    def test_tied_distinct_titles_are_skipped_but_identical_ties_are_safe(self):
        rows = [
            (3, "Old", "2026-01-01", ""),
            (3, "First", "2026-01-02", ""),
            (3, "Second", "2026-01-02", ""),
            (4, "Old", "2026-01-01", ""),
            (4, "New", "2026-01-02", "a"),
            (4, "New", "2026-01-02", "b"),
        ]
        self.assertEqual(
            self.select(rows), {3: (None, "ambiguous"), 4: ("New", "ready")}
        )

    def test_only_distinct_non_null_titles_make_candidates(self):
        rows = [
            (5, "One", "2026-01-01", ""),
            (5, None, "2026-01-02", ""),
            (6, "One", "2026-01-01", ""),
            (6, "One", "2026-01-02", ""),
            (None, "A", "2026-01-01", ""),
            (None, "B", "2026-01-02", ""),
        ]
        self.assertEqual(self.select(rows), {})


class CleanseInvocationTests(unittest.TestCase):
    def test_runs_combined_script_and_returns_summary(self):
        expected = {"run_id": "test", "candidate_count": 0}
        client = Mock()
        client.query.return_value.result.return_value = iter([expected])

        self.assertEqual(cleanse.run_cleanse(client), expected)
        query = client.query.call_args.args[0]
        self.assertNotIn("-- TITLE_CHOICES_QUERY", query)
        self.assertIn("HAVING COUNT(DISTINCT `Photo Title`) > 1", query)
        self.assertEqual(client.query.call_args.kwargs["location"], "europe-west9")

    def test_query_errors_propagate(self):
        client = Mock()
        client.query.side_effect = RuntimeError("BigQuery failed")
        with self.assertRaisesRegex(RuntimeError, "BigQuery failed"):
            cleanse.run_cleanse(client)


class BackupAndUpdateTests(unittest.TestCase):
    def test_backup_covers_all_ready_rows_and_update_only_changes_title(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.create_function("STARTS_WITH", 2, lambda text, prefix: text.startswith(prefix))
        db.execute(
            "CREATE TABLE stats (`Photo ID` INTEGER, `Photo Title` TEXT, "
            "updated_at TEXT, Link TEXT, views INTEGER)"
        )
        rows = [
            (1, "PXL_1", "2026-01-01", "a", 10),
            (1, "Title", "2026-01-02", "b", 20),
            (1, None, "2026-01-03", "c", 30),
            (2, "IMG_1", "2026-01-01", "d", 40),
            (2, "CR2_1", "2026-01-02", "e", 50),
            (3, "Unchanged", "2026-01-01", "f", 60),
        ]
        db.executemany("INSERT INTO stats VALUES (?, ?, ?, ?, ?)", rows)
        selection = (SQL_DIR / "select_title_changes.sql").read_text(
            encoding="utf-8"
        ).replace(TARGET, "stats")
        db.execute("CREATE TEMP TABLE title_choices AS " + selection)
        db.execute(
            "CREATE TABLE backup (backup_run_id TEXT, backup_at TEXT, "
            "`Photo ID` INTEGER, `Photo Title` TEXT, updated_at TEXT, "
            "Link TEXT, views INTEGER)"
        )
        script = (SQL_DIR / "cleanse_titles.sql").read_text(encoding="utf-8")
        statements = script.split("  INSERT INTO ", 1)[1].split(
            "  SET updated_rows", 1
        )[0]
        statements = "INSERT INTO " + statements
        statements = statements.replace(
            "`flickrstats-492309.flickrstats.flickrstats_titles_changed`", "backup"
        ).replace(TARGET, "stats")
        statements = statements.replace("run_id, CURRENT_TIMESTAMP()", "'run-1', CURRENT_TIMESTAMP")
        db.executescript(statements)

        backed_up = db.execute(
            "SELECT `Photo ID`, `Photo Title`, updated_at, Link, views FROM backup"
        ).fetchall()
        self.assertCountEqual(backed_up, rows[:3])
        updated = db.execute(
            "SELECT `Photo ID`, `Photo Title`, updated_at, Link, views FROM stats"
        ).fetchall()
        self.assertCountEqual(
            updated,
            [(1, "Title", row[2], row[3], row[4]) for row in rows[:3]] + rows[3:],
        )
        self.assertEqual(list(db.execute(selection)), [(2, None, "no_valid_title")])


if __name__ == "__main__":
    unittest.main()
