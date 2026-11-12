import uuid

import pytest

from config.settings import settings
from pages.compose_page import ComposePage
from pages.mailbox_page import MailboxPage


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.two_account
def test_send_email_arrives_in_receiver_inbox(receiver_driver, sender_driver):
    subject = f"QA-{uuid.uuid4().hex[:8]}"

    sender = MailboxPage(sender_driver)
    sender_driver.execute_cdp_cmd("Page.bringToFront", {})
    sender.open_compose()
    ComposePage(sender_driver).compose_and_send(
        to=settings.receiver.email,
        subject=subject,
        body="Automated test message",
    )

    sender.open_folder("sent")
    assert sender.has_message(subject, timeout=20), "Message missing from sender's Sent folder"

    receiver = MailboxPage(receiver_driver)
    receiver.wait_for_message(subject, folder="inbox", timeout=60)
    assert receiver.has_message(subject), "Message did not arrive in receiver's inbox"


@pytest.mark.regression
@pytest.mark.p0
def test_send_without_recipient_is_blocked(sender_driver):
    subject = f"QA-NORECIPIENT-{uuid.uuid4().hex[:8]}"
    mailbox = MailboxPage(sender_driver)
    mailbox.open_compose()

    compose = ComposePage(sender_driver).wait_until_open()
    compose.set_subject(subject)
    compose.set_body("No recipient set")
    compose.click_send()

    assert compose.is_visible(ComposePage.NO_RECIPIENT_MODAL, timeout=10), \
        "Proton did not warn about the missing recipient"
    compose.dismiss_no_recipient_dialog()
    assert compose.is_still_open(), "Composer closed even though no recipient was set"
    compose.close()

    mailbox.open_folder("sent")
    assert not mailbox.has_message(subject, timeout=5), "Message was sent without a recipient"


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.parametrize("bad_address", ["not-an-email", "user@"])
def test_send_to_invalid_address_is_blocked(sender_driver, bad_address):
    subject = f"QA-INVALID-{uuid.uuid4().hex[:8]}"
    mailbox = MailboxPage(sender_driver)
    mailbox.open_compose()

    compose = ComposePage(sender_driver).wait_until_open()
    compose.add_recipient_unchecked(bad_address)
    compose.set_subject(subject)
    compose.set_body("Invalid recipient")
    compose.click_send()

    assert compose.is_visible(ComposePage.INVALID_ADDRESS, timeout=10), \
        f"Proton showed no 'not valid' message for '{bad_address}'"
    assert compose.is_still_open(), f"Composer closed after sending to '{bad_address}'"
    compose.close()

    mailbox.open_folder("sent")
    assert not mailbox.has_message(subject, timeout=5), f"Message was sent to '{bad_address}'"