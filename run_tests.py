"""Run the tests listed in TESTS, in the order listed.

    python run_tests.py                  -> run everything that is not commented out below
    python run_tests.py test_x test_y    -> run just these (overrides the list)
    python run_tests.py --list           -> show every available test name and whether it is selected

Each run writes its own report: reports/report_<date>_<time>.html
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Put a '#' in front of any test you do not want to run.  Order = run order.
# ---------------------------------------------------------------------------
TESTS = [
    # authentication
    "test_valid_login_reaches_inbox",
    "test_invalid_password_shows_error",
    # compose
    "test_send_email_arrives_in_receiver_inbox",
    "test_send_without_recipient_is_blocked",
    "test_send_to_invalid_address_is_blocked",
    # drafts
    "test_draft_is_saved_and_reopens_with_content",
    "test_deleted_draft_is_removed_from_drafts",
    # inbox actions
    "test_star_and_unstar_message",
    "test_mark_message_read_and_unread",
    "test_move_to_trash_and_restore",
    # search
    "test_keyword_search_finds_only_matching_message",
    "test_search_with_no_match_returns_no_results",
    "test_advanced_search_keyword_and_location",
    # filters
    "test_filter_stars_matching_incoming_message",
    # undo send
    "test_undo_send_cancels_delivery",
    # attachments
    "test_email_with_attachment_arrives_with_attachment",
]
# ---------------------------------------------------------------------------

TESTS_DIR = Path(__file__).parent / "tests"
DEF_RE = re.compile(r"^(?:async\s+)?def\s+(test_\w+)\s*\(", re.MULTILINE)


def available_tests():
    """Map test function name -> pytest node id, by scanning tests/test_*.py."""
    found = {}
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        for name in DEF_RE.findall(path.read_text(encoding="utf-8")):
            found[name] = f"{path.relative_to(TESTS_DIR.parent).as_posix()}::{name}"
    return found


def main(argv):
    available = available_tests()

    if argv == ["--list"]:
        selected = set(TESTS)
        for name in available:
            print(f"[{'x' if name in selected else ' '}] {name}")
        return 0

    names = argv or TESTS
    unknown = [n for n in names if n not in available]
    if unknown:
        print("Unknown test name(s):", ", ".join(unknown))
        print("Run 'python run_tests.py --list' to see the valid names.")
        return 2
    if not names:
        print("No tests selected. Un-comment some names in TESTS.")
        return 2

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report = Path("reports") / f"report_{stamp}.html"
    args = [available[n] for n in names] + ["-v", f"--html={report}", "--self-contained-html"]
    print(f"Running {len(names)} test(s); report -> {report}")
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))