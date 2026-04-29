import time
import yaml
from monitor import tail_log, parse_line
from baseline import BaselineTracker
from detector import AnomalyDetector
from blocker import Blocker
from unbanner import Unbanner
from notifier import Notifier
from audit import AuditLog
from dashboard import Dashboard

def load_config():
    with open("/home/ubuntu/hng-stage3/detector/config.yaml") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    start_time = time.time()
    print("[MAIN] Starting HNG Anomaly Detector...")
    audit = AuditLog(config["log"]["audit_log"])
    baseline = BaselineTracker(
        window_minutes=config["detection"]["baseline_window_minutes"],
        recalc_interval=config["detection"]["recalculation_interval"]
    )
    detector = AnomalyDetector(config, baseline)
    blocker = Blocker(config)
    notifier = Notifier(config)
    unbanner = Unbanner(blocker, notifier, audit)
    dashboard = Dashboard(config, detector, blocker, baseline, start_time)
    unbanner.start()
    dashboard.start(port=config["dashboard"]["port"])
    print("[MAIN] Dashboard on port " + str(config["dashboard"]["port"]))
    log_path = config["log"]["nginx_log"]
    print("[MAIN] Tailing: " + log_path)
    recently_banned = {}
    last_global_alert = 0
    for line in tail_log(log_path):
        entry = parse_line(line)
        if not entry:
            continue
        ip = entry["ip"]
        is_error = entry["status"] >= 400
        baseline.record_request(is_error=is_error)
        detector.record(ip, is_error=is_error)
        if blocker.is_banned(ip):
            continue
        now = time.time()
        if ip not in recently_banned or now - recently_banned.get(ip, 0) > 60:
            flagged, condition, rate = detector.check_ip(ip)
            if flagged:
                duration = blocker.ban(ip)
                recently_banned[ip] = now
                notifier.ban_alert(ip, condition, rate, baseline.effective_mean, duration)
                audit.log_ban(ip, condition, rate, baseline.effective_mean, duration)
                print("[BAN] " + ip)
        if now - last_global_alert > 60:
            g_flagged, g_condition, g_rate = detector.check_global()
            if g_flagged:
                notifier.global_alert(g_condition, g_rate, baseline.effective_mean)
                last_global_alert = now

if __name__ == "__main__":
    main()
