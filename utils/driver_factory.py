import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config.settings import settings

def create_driver(profile_dir: str | None = None):
    options = Options()
    if settings.headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-background-timer-throttling")
    profile = profile_dir or settings.profile_dir
    if profile:
        options.add_argument(f"--user-data-dir={os.path.abspath(profile)}")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.implicitly_wait(0)
    return driver
