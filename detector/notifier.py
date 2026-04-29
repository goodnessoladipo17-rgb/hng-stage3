import requests
import json
from datetime import datetime

class Notifier:
    def __init__(self, config):
        self.webhook_url = config['slack']['webhook_url']

    def send(self, message):
        if not self.webhook_url or self.webhook_url == "YOUR_SLACK_WEBHOOK_URL":
            print(f"[SLACK] {message}")
            return
        try:
            requests.post(self.webhook_url, json={"text": message}, timeout=5)
        except Exception as e:
            print(f"Slack error: {e}")

    def ban_alert(self, ip, condition, rate, baseline, duration):
        dur_str = f"{duration}s" if duration > 0 else "permanent"
        msg = (
            f":rotating_light: *BAN* | IP: `{ip}`\n"
            f"Condition: {condition}\n"
            f"Rate: {rate:.2f} req/s | Baseline: {baseline:.2f} req/s\n"
            f"Duration: {dur_str}\n"
            f"Time: {datetime.utcnow().isoformat()}Z"
        )
        self.send(msg)

    def unban_alert(self, ip, duration):
        msg = (
            f":white_check_mark: *UNBAN* | IP: `{ip}`\n"
            f"Ban duration was: {duration}s\n"
            f"Time: {datetime.utcnow().isoformat()}Z"
        )
        self.send(msg)

    def global_alert(self, condition, rate, baseline):
        msg = (
            f":warning: *GLOBAL ANOMALY*\n"
            f"Condition: {condition}\n"
            f"Rate: {rate:.2f} req/s | Baseline: {baseline:.2f} req/s\n"
            f"Time: {datetime.utcnow().isoformat()}Z"
        )
        self.send(msg)
