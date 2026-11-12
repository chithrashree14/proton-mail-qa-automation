import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Account:
    username: str
    password: str = field(repr=False)

    @property
    def email(self):
        return self.username if "@" in self.username else f"{self.username}@proton.me"


@dataclass(frozen=True)
class Settings:
    login_url: str = "https://account.proton.me/mail"
    mail_url: str = "https://mail.proton.me"
    headless: bool = os.getenv("HEADLESS", "false").lower() == "true"
    timeout: int = int(os.getenv("DEFAULT_TIMEOUT", "20"))
    profile_dir: str = os.getenv("CHROME_PROFILE_DIR", "")
    sender: Account = Account(os.getenv("SENDER_USER", ""), os.getenv("SENDER_PASS", ""))
    receiver: Account = Account(os.getenv("RECEIVER_USER", ""), os.getenv("RECEIVER_PASS", ""))


settings = Settings()