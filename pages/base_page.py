from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException,
)
from config.settings import settings



def by_testid(value):
    return (By.CSS_SELECTOR, f"[data-testid='{value}']")

SPOTLIGHT_NOT_NOW = (By.XPATH, "//*[@data-testid='spotlight-inner']//button[normalize-space(.)='Not now']")
SPOTLIGHT_CLOSE = by_testid("spotlight-inner-close-button")

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, settings.timeout)

    def open(self, url):
        self.driver.get(url)

    def find(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def wait_for(self, locator, timeout=20):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def click(self, locator):
        for attempt in (1, 2, 3):
            try:
                self.wait.until(EC.element_to_be_clickable(locator)).click()
                return
            except ElementClickInterceptedException:
                if attempt == 3:
                    raise
                self.dismiss_popups()
            except StaleElementReferenceException:
                if attempt == 3:
                    raise  # page re-rendered; look the element up again

    def dismiss_popups(self):
        """Close Proton promo pop-ups that can cover the page."""
        for locator in (SPOTLIGHT_NOT_NOW, SPOTLIGHT_CLOSE):
            for element in self.driver.find_elements(*locator):
                try:
                    if element.is_displayed():
                        self.driver.execute_script("arguments[0].click();", element)
                except WebDriverException:
                    pass

    def type(self, locator, text):
        element = self.visible(locator)
        element.clear()
        element.send_keys(text)

    def text_of(self, locator):
        return self.visible(locator).text

    def is_visible(self, locator, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except Exception:
            return False

    def wait_for_url_contains(self, fragment):
        self.wait.until(EC.url_contains(fragment))