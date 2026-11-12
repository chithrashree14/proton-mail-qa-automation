from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage, by_testid

FOLDERS = {
    "inbox": "navigation-link:inbox",
    "sent": "navigation-link:all-sent",
    "drafts": "navigation-link:all-drafts",
    "starred": "navigation-link:starred",
}

SEARCH_LOCATIONS = {
    "all": "location-15",
    "drafts": "location-1",
    "sent": "location-2",
}


class MailboxPage(BasePage):
    COMPOSE_BUTTON = by_testid("sidebar:compose")

    # toolbar (visible once a message is selected)
    TOOLBAR_READ = by_testid("toolbar:read")
    TOOLBAR_TRASH = by_testid("toolbar:movetotrash")
    TOOLBAR_UNREAD = (
        By.XPATH,
        "//button[@data-testid='toolbar:unread' or @title='Mark as unread' "
        "or normalize-space(.)='Mark as unread']",
    )
    TOOLBAR_RESTORE = (
        By.XPATH,
        "//button[starts-with(@data-testid,'toolbar:') and (contains(@data-testid,'inbox') "
        "or contains(@title,'inbox') or contains(.,'Move to inbox'))]",
    )

    # sidebar
    SIDEBAR_MORE = (By.XPATH, "//button[normalize-space(.)='More']")
    TRASH_LINK = (By.XPATH, "//a[contains(@data-testid,'trash')]")

    # message list
    ROW_CHECKBOX = (By.CSS_SELECTOR, "[data-testid='item-checkbox']")
    ANY_MESSAGE = (By.CSS_SELECTOR, "[data-testid^='message-item:']")
    NO_RESULTS = (By.XPATH, "//*[normalize-space(text())='No results found']")

    # search
    SEARCH_INPUT = by_testid("search-keyword")
    ADV_KEYWORD = by_testid("input-input-element")
    ADV_SUBMIT = by_testid("advanced-search:submit")

    # undo
    UNDO_BUTTON = (By.XPATH, "//*[self::button or self::a][normalize-space(.)='Undo']")
    SEARCH_HINT = (By.XPATH, "//*[contains(., 'looking for') and contains(., 'Include Spam')]")
    

    def wait_for_search_settled(self, timeout=20):
        self.wait.until(lambda d: d.find_elements(*self.NO_RESULTS) or d.find_elements(*self.SEARCH_HINT))

    @staticmethod
    def message_locator(subject):
        return by_testid(f"message-item:{subject}")

    def _wait(self, timeout=15):
        return WebDriverWait(
            self.driver, timeout, ignored_exceptions=(StaleElementReferenceException,)
        )

    # --- page state -------------------------------------------------------

    def wait_until_loaded(self, timeout=45):
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.COMPOSE_BUTTON)
        )
        return self

    def wait_for_title_contains(self, text):
        self.wait.until(EC.title_contains(text))

    # --- navigation -------------------------------------------------------

    def open_compose(self):
        self.click(self.COMPOSE_BUTTON)

    def open_folder(self, name):
        self.click(by_testid(FOLDERS[name]))

    def open_trash(self):
        if not self.is_visible(self.TRASH_LINK, timeout=1):
            self.click(self.SIDEBAR_MORE)
        self.click(self.TRASH_LINK)

    # --- message list -----------------------------------------------------

    def has_message(self, subject, timeout=5):
        return self.is_visible(self.message_locator(subject), timeout=timeout)

    def result_count(self):
        """Count only rows that are actually visible (Proton keeps hidden rows in the DOM)."""
        return self.driver.execute_script(
            "return Array.from(document.querySelectorAll(\"[data-testid^='message-item:']\"))"
            ".filter(e => e.offsetParent !== null).length;"
        )

    def wait_for_no_results(self, timeout=20):
        self.wait_for(self.NO_RESULTS, timeout)

    def wait_for_message(self, subject, folder="inbox", timeout=60):
        """Poll for a message, re-opening the folder between attempts instead of sleeping."""
        locator = self.message_locator(subject)
        end = WebDriverWait(self.driver, timeout)

        def _found(_):
            if self.is_visible(locator, timeout=3):
                return True
            self.open_folder(folder)
            return False

        end.until(_found)
        return self

    def wait_until_gone(self, subject, timeout=10):
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.message_locator(subject))
        )

    def open_draft(self, subject):
        self.click(self.message_locator(subject))

    # --- message actions --------------------------------------------------

    def toggle_star(self, subject):
        locator = (
            By.XPATH,
            f"//*[@data-testid='message-item:{subject}']//*[starts-with(@data-testid, 'item-star-')]",
        )
        self.click(locator)

    def select_message(self, subject):
        row = self.visible(self.message_locator(subject))
        box = row.find_element(*self.ROW_CHECKBOX)
        self.driver.execute_script("arguments[0].click();", box)
        self._wait().until(
            lambda d: d.find_element(*self.message_locator(subject))
            .find_element(*self.ROW_CHECKBOX)
            .is_selected()
        )

    def is_unread(self, subject):
        row = self.driver.find_element(*self.message_locator(subject))
        return "Unread email" in self.driver.execute_script(
            "return arguments[0].innerText;", row
        )

    def wait_until_unread_state(self, subject, unread):
        self._wait().until(lambda d: self.is_unread(subject) == unread)

    # --- search -----------------------------------------------------------

    def _open_search_panel(self):
        """Open the search dropdown and return its keyword field."""
        box = self.visible(self.SEARCH_INPUT)
        for _ in range(3):
            box.click()
            if self.is_visible(self.ADV_KEYWORD, timeout=3):
                break
            self.driver.execute_script("arguments[0].focus();", box)
        return self.visible(self.ADV_KEYWORD)

    def advanced_search(self, keyword, location="all"):
        field = self._open_search_panel()
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(Keys.BACKSPACE)
        field.send_keys(keyword)
        self.click(by_testid(SEARCH_LOCATIONS[location]))
        self.click(self.ADV_SUBMIT)

    def search(self, text):
        self.advanced_search(text, "all")

    def has_attachment_icon(self, subject, timeout=10):
        locator = (
            By.XPATH,
            f"//*[@data-testid='message-item:{subject}']"
            "//*[@data-testid='item-attachment-icon-paper-clip']",
        )
        return self.is_visible(locator, timeout=timeout)

    # --- undo -----------------------------------------------------------

    def click_undo(self, timeout=15):
        button = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(self.UNDO_BUTTON))
        self.driver.execute_script("arguments[0].click();", button)