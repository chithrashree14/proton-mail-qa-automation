import uuid

import pytest

from pages.mailbox_page import MailboxPage


@pytest.mark.regression
@pytest.mark.p1
def test_keyword_search_finds_only_matching_message(target_and_control):
    mailbox, target, control = target_and_control

    mailbox.search(target)

    assert mailbox.has_message(target, timeout=20), "Search did not return the matching message"
    mailbox.wait_until_gone(control, timeout=15)


@pytest.mark.regression
@pytest.mark.p2
def test_search_with_no_match_returns_no_results(sender_driver, target_and_control):
    """A keyword that matches nothing must not show any existing message."""
    mailbox, _, control_subject = target_and_control
    keyword = f"nomatch-{uuid.uuid4().hex}"

    # Precondition: the control message really exists, so "not shown" proves filtering
    assert mailbox.wait_for_message(control_subject), "Precondition failed: control message not found"

    mailbox.advanced_search(keyword)
    mailbox.wait_for_search_settled()
    mailbox.wait_until_gone(control_subject)

    assert not mailbox.has_message(keyword)

@pytest.mark.regression
@pytest.mark.p1
def test_advanced_search_keyword_and_location(own_message):
    mailbox, subject = own_message

    # The message was sent, so it lives in Sent/Inbox - never in Drafts
    mailbox.advanced_search(subject, "drafts")
    mailbox.wait_for_search_settled()
    mailbox.wait_until_gone(subject, timeout=15)

    assert not mailbox.has_message(subject), "A sent message must not match a search in Drafts"