import uuid

import pytest

from pages.compose_page import ComposePage
from pages.mailbox_page import MailboxPage


def create_saved_draft(driver, subject, body):
    mailbox = MailboxPage(driver)
    mailbox.open_compose()
    compose = ComposePage(driver).wait_until_open()
    compose.set_subject(subject)
    compose.set_body(body)
    compose.wait_until_saved()
    return mailbox, compose


@pytest.mark.regression
@pytest.mark.p1
def test_draft_is_saved_and_reopens_with_content(sender_driver):
    subject = f"QA-DRAFT-{uuid.uuid4().hex[:8]}"
    body = "Draft body text"

    mailbox, compose = create_saved_draft(sender_driver, subject, body)
    compose.close()

    mailbox.wait_for_message(subject, folder="drafts", timeout=30)
    mailbox.open_draft(subject)

    reopened = ComposePage(sender_driver).wait_until_open()
    assert reopened.subject_value() == subject
    assert body in reopened.body_text()


@pytest.mark.regression
@pytest.mark.p1
def test_deleted_draft_is_removed_from_drafts(sender_driver):
    subject = f"QA-DRAFT-DEL-{uuid.uuid4().hex[:8]}"

    mailbox, compose = create_saved_draft(sender_driver, subject, "To be deleted")
    compose.delete_draft()

    mailbox.open_folder("drafts")
    assert not mailbox.has_message(subject, timeout=5), "Deleted draft still listed in Drafts"