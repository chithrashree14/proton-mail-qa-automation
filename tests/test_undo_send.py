import uuid

import pytest

from config.settings import settings
from pages.compose_page import ComposePage
from pages.mailbox_page import MailboxPage


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.async_flow
def test_undo_send_cancels_delivery(sender_driver):
    subject = f"QA-UNDO-{uuid.uuid4().hex[:8]}"
    mailbox = MailboxPage(sender_driver)
    mailbox.open_compose()
    ComposePage(sender_driver).compose_and_send(settings.sender.email, subject, "Undo me")

    mailbox.click_undo()

    # Undo may reopen the composer with the draft; if it does, check it and close it.
    compose = ComposePage(sender_driver)
    if compose.is_visible(ComposePage.SUBJECT, timeout=10):
        assert compose.subject_value() == subject, "Undo restored the wrong draft"
        compose.close()

    # Positive check first: the draft is back. Only then is "not in Sent" meaningful.
    mailbox.wait_for_message(subject, folder="drafts", timeout=30)
    assert mailbox.has_message(subject), "Draft missing from Drafts after undo"

    mailbox.open_folder("sent")
    assert not mailbox.has_message(subject, timeout=5), "Message was sent despite Undo"

    mailbox.open_folder("inbox")
    assert not mailbox.has_message(subject, timeout=5), "Message was delivered despite Undo"