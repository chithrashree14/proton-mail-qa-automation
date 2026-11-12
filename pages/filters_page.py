from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage, by_testid

FILTERS_URL = "https://account.proton.me/mail/filters"


class FiltersPage(BasePage):
    ADD_FILTER = (By.XPATH, "//button[normalize-space(.)='Add filter']")
    NAME_INPUT = by_testid("filter-modal:name-input")
    NEXT = by_testid("filter-modal:next-button")  # reads "Next", then "Preview" on the Actions step
    KEYWORD = (By.XPATH, "//input[@placeholder='Type text or keyword']")
    INSERT = (By.XPATH, "//button[normalize-space(.)='Insert']")
    STARRED_LABEL = (By.XPATH, "//label[normalize-space(.)='Starred']")
    SAVE = (By.XPATH, "//button[@type='submit' and normalize-space(.)='Save']")
    BACK_TO_APP = by_testid("account:back-to-app")
    GET_MORE = (By.XPATH, "//button[contains(normalize-space(.), 'Get more filters')]")
    FILTERS_URL = "https://account.proton.me/mail/filters"

    @staticmethod
    def filter_row(name):
        return (By.XPATH, f"//*[contains(text(), '{name}')]")

    def load(self, check_limit=True):
        for attempt in (1, 2):
            self.driver.get(self.FILTERS_URL)
            try:
                WebDriverWait(self.driver, 40).until(
                    lambda d: d.find_elements(*self.ADD_FILTER)
                              or d.find_elements(*self.GET_MORE)
                )
                break
            except TimeoutException:
                if attempt == 2:
                    raise
        if check_limit:
            assert not self.is_visible(self.GET_MORE, timeout=5), (
                "Free-plan filter limit reached - delete old 'QA filter' entries "
                "in Settings > Filters and re-run"
            )
        return self

    def create_filter_that_stars(self, name, keyword):
        """Create a filter: subject contains <keyword>  ->  mark as Starred."""
        self.click(self.ADD_FILTER)
        self.type(self.NAME_INPUT, name)
        self.click(self.NEXT)  # Name -> Conditions

        self.type(self.KEYWORD, keyword)
        self.click(self.INSERT)  # adds the condition; Next stays disabled until this is done
        self.click(self.NEXT)  # Conditions -> Actions

        label = self.visible(self.STARRED_LABEL)
        label.click()
        WebDriverWait(
            self.driver, 10, ignored_exceptions=(StaleElementReferenceException,)
        ).until(lambda d: d.execute_script("return arguments[0].control.checked;", label))
        self.click(self.NEXT)  # Actions -> Preview

        self.click(self.SAVE)
        self.wait.until(EC.invisibility_of_element_located(self.SAVE))
        self.visible(self.filter_row(name))

    def back_to_mailbox(self):
        self.click(self.BACK_TO_APP)

    def delete_qa_filters(self):
        """Remove every filter whose name starts with 'QA filter' (test data only)."""
        self.load(check_limit=False)
        while True:
            names = [e for e in self.driver.find_elements(
                By.XPATH, "//*[starts-with(normalize-space(text()), 'QA filter')]") if e.is_displayed()]
            if not names:
                return
            name_el = names[0]
            row = name_el.find_element(
                By.XPATH, "./ancestor::*[.//button[normalize-space(.)='Edit']][1]")
            menu_button = row.find_elements(By.TAG_NAME, "button")[-1]      # the arrow next to Edit
            self.driver.execute_script("arguments[0].click();", menu_button)
            delete_item = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[self::button or @role='menuitem'][normalize-space(.)='Delete']")))
            self.driver.execute_script("arguments[0].click();", delete_item)
            confirm = self.wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//button[normalize-space(.)='Delete']")))[-1]
            self.driver.execute_script("arguments[0].click();", confirm)
            self.wait.until(EC.staleness_of(name_el))