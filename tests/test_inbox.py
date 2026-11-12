import uuid

import pytest

from config.settings import settings
from pages.compose_page import ComposePage
from pages.mailbox_page import MailboxPage



@pytest.fixture
def own_message(sender_driver):
    """Send a uniquely named message to the sender's own inbox and return (mailbox, subject)."""
    subject = f"QA-INBOX-{uuid.uuid4().hex[:8]}"
    mailbox = MailboxPage(sender_driver)
    mailbox.open_compose()
    ComposePage(sender_driver).compose_and_send(
        settings.sender.email, subject, "Inbox action test"
    )
    mailbox.wait_for_message(subject, folder="inbox", timeout=60)
    return mailbox, subject


@pytest.mark.regression
@pytest.mark.p1
def test_star_and_unstar_message(own_message):
    mailbox, subject = own_message

    mailbox.toggle_star(subject)
    mailbox.open_folder("starred")
    assert mailbox.has_message(subject, timeout=15), "Starred message not listed in Starred"

    mailbox.toggle_star(subject)
    mailbox.wait_until_gone(subject, timeout=15)

    mailbox.open_folder("inbox")
    assert mailbox.has_message(subject, timeout=15), "Unstarred message missing from Inbox"

@pytest.mark.regression
@pytest.mark.p1
def test_mark_message_read_and_unread(own_message):
    mailbox, subject = own_message
    assert mailbox.is_unread(subject), "A newly received message should start unread"

    mailbox.select_message(subject)
    mailbox.click(MailboxPage.TOOLBAR_READ)
    mailbox.wait_until_unread_state(subject, unread=False)

    mailbox.click(MailboxPage.TOOLBAR_UNREAD)
    mailbox.wait_until_unread_state(subject, unread=True)


@pytest.mark.regression
@pytest.mark.p1
def test_move_to_trash_and_restore(own_message):
    mailbox, subject = own_message

    mailbox.select_message(subject)
    print("RESTORE MATCHES:", [(b.get_attribute("data-testid"), b.get_attribute("title")) for b in mailbox.driver.find_elements(*MailboxPage.TOOLBAR_RESTORE)])
    mailbox.click(MailboxPage.TOOLBAR_TRASH)
    mailbox.wait_until_gone(subject, timeout=15)

    mailbox.open_trash()
    assert mailbox.has_message(subject, timeout=15), "Trashed message not found in Trash"

    mailbox.select_message(subject)
    mailbox.click(MailboxPage.TOOLBAR_RESTORE)
    mailbox.wait_until_gone(subject, timeout=15)

    mailbox.wait_for_message(subject, folder="inbox", timeout=45)
    assert mailbox.has_message(subject), "Restored message missing from Inbox"