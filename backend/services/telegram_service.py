import os
import requests


class TelegramService:
    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    def send_alert(self, message: str, image_path: str | None = None) -> bool:
        if not self.token or not self.chat_id:
            return False
        if image_path:
            url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
            with open(image_path, "rb") as image:
                return requests.post(url, data={"chat_id": self.chat_id, "caption": message}, files={"photo": image}, timeout=15).ok
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        return requests.post(url, data={"chat_id": self.chat_id, "text": message}, timeout=15).ok
