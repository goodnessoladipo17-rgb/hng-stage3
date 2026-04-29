import time
import threading

class Unbanner:
    def __init__(self, blocker, notifier, audit_log):
        self.blocker = blocker
        self.notifier = notifier
        self.audit_log = audit_log
        self.running = True

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        while self.running:
            expired = self.blocker.check_expired_bans()
            for ip in expired:
                info = self.blocker.banned_ips.get(ip, {})
                duration = info.get('duration', 0)
                self.blocker.unban(ip)
                self.notifier.unban_alert(ip, duration)
                self.audit_log.log_unban(ip, duration)
                print(f"[UNBAN] {ip} released after {duration}s")
            time.sleep(10)

    def stop(self):
        self.running = False
