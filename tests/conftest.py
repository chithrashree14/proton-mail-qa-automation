import os

import pytest
from pytest_html import extras
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException
from config.settings import settings
from pages.login_page import LoginPage
from pages.mailbox_page import MailboxPage
from utils.driver_factory import create_driver
from selenium.webdriver.support.ui import WebDriverWait
import uuid
from pages.compose_page import ComposePage

ARTIFACTS_DIR = os.path.join("reports", "artifacts")
DRIVER_FIXTURES = ("driver", "sender_driver", "receiver_driver")

from selenium.common.exceptions import TimeoutException

PROFILES = {"sender": ".chrome-profile-sender", "receiver": ".chrome-profile-receiver"}


def _open_session(name, account):
    browser = create_driver(profile_dir=PROFILES[name])
    try:
        browser.get(settings.mail_url)
        try:
            MailboxPage(browser).wait_until_loaded(timeout=45)       # saved session
        except TimeoutException:
            browser.get(settings.mail_url)                           # slow load: reload once
            try:
                MailboxPage(browser).wait_until_loaded(timeout=60)
            except TimeoutException:
                _login(browser, account, name)                       # real login as last resort
    except BaseException:
        browser.quit()                                               # never leave the profile locked
        raise
    return browser

def save_evidence(browser, label):
    """Best-effort: a dead browser must never crash the test run."""
    try:
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        base = os.path.join(ARTIFACTS_DIR, label)
        browser.save_screenshot(base + ".png")
        with open(base + ".html", "w", encoding="utf-8") as f:
            f.write(browser.page_source)
        print(f"EVIDENCE SAVED: {os.path.abspath(base)}.png")
        return True
    except WebDriverException as exc:
        print(f"EVIDENCE NOT SAVED ({label}): browser unavailable ({type(exc).__name__})")
        return False


def _login_outcome(browser):
    """Return 'mailbox' once the inbox is usable, 'form' if the sign-in form has reset."""
    if any(e.is_displayed() for e in browser.find_elements(*MailboxPage.COMPOSE_BUTTON)):
        return "mailbox"
    if any(e.is_displayed() for e in browser.find_elements(*LoginPage.USERNAME)):
        return "form"
    return False


def _wait_for_login_outcome(browser, timeout=60):
    return WebDriverWait(
        browser, timeout, ignored_exceptions=(StaleElementReferenceException,)
    ).until(_login_outcome)


def _login(browser, account, label):
    """Log in. Two known Proton quirks are handled, each logged with a screenshot:
    1. The sign-in form resets to empty (session-expired redirect): submit credentials once more.
    2. Credentials are accepted but the mail app stalls while loading: reload the page once.
    Any other failure, or a second failure, fails the test."""
    for attempt in (1, 2):
        LoginPage(browser).load().login(account.username, account.password)
        try:
            outcome = _wait_for_login_outcome(browser)
        except TimeoutException:
            print(f"LOGIN TIMEOUT ({label}) attempt {attempt} url={browser.current_url} | title={browser.title}")
            save_evidence(browser, f"login_timeout__{label}__attempt{attempt}")
            if "mail.proton.me" not in browser.current_url:
                raise
            print(f"MAIL APP STALLED ({label}): reloading once")
            browser.get(settings.mail_url)
            try:
                outcome = _wait_for_login_outcome(browser)
            except TimeoutException:
                save_evidence(browser, f"login_timeout__{label}__after_reload")
                raise
        if outcome == "mailbox":
            return browser
        print(f"LOGIN FORM RESET ({label}) attempt {attempt} url={browser.current_url}")
        save_evidence(browser, f"login_form_reset__{label}__attempt{attempt}")
    raise AssertionError(f"Sign-in form kept resetting for {label} after 2 attempts")

@pytest.fixture
def driver():
    browser = create_driver()
    yield browser
    browser.quit()


@pytest.fixture
def sender_driver(request):
    browser = _open_session("sender", settings.sender)
    yield browser
    browser.quit()

@pytest.fixture
def login(driver):
    def _login_as(account, label="user"):
        return _login(driver, account, label)
    return _login_as

@pytest.fixture
def receiver_driver(request):
    browser = _open_session("receiver", settings.receiver)
    yield browser
    browser.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when in ("setup", "call") and report.failed:
        for fixture_name in DRIVER_FIXTURES:
            browser = item.funcargs.get(fixture_name)
            if not browser:
                continue
            name = item.nodeid.replace("/", "_").replace("::", "__") + f"__{fixture_name}"
            if not save_evidence(browser, name):
                continue
            try:
                report.extras = getattr(report, "extras", []) + [
                    extras.png(browser.get_screenshot_as_base64())
                ]
            except WebDriverException:
                pass

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

@pytest.fixture
def target_and_control(own_message):
    """own_message is the search target; the control is any other message already listed."""
    mailbox, target = own_message
    testids = mailbox.driver.execute_script(
        "return Array.from(document.querySelectorAll(\"[data-testid^='message-item:']\"))"
        ".filter(e => e.offsetParent !== null).map(e => e.getAttribute('data-testid'));"
    )
    others = [t.split(":", 1)[1] for t in testids]
    safe = [s for s in others if s != target and not any(c in s for c in "'\"\\")]
    assert safe, "Need at least one other message in the inbox to act as the control"
    return mailbox, target, safe[0]