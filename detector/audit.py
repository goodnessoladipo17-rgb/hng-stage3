import json
from datetime import datetime

class AuditLog:
    def __init__(self, log_path):
        self.log_path = log_path

    def _write(self, entry):
        entry['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        line = f"[{entry['timestamp']}] {entry['action']} {entry.get('ip', 'global')} | {entry.get('condition', '')} | rate={entry.get('rate', 0):.2f} | baseline={entry.get('baseline', 0):.2f} | duration={entry.get('duration', '')}"
        print(line)
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"Audit log error: {e}")

    def log_ban(self, ip, condition, rate, baseline, duration):
        self._write({
            'action': 'BAN',
            'ip': ip,
            'condition': condition,
            'rate': rate,
            'baseline': baseline,
            'duration': duration
        })

    def log_unban(self, ip, duration):
        self._write({
            'action': 'UNBAN',
            'ip': ip,
            'condition': 'expired',
            'rate': 0,
            'baseline': 0,
            'duration': duration
        })

    def log_baseline(self, mean, stddev, samples):
        self._write({
            'action': 'BASELINE_RECALC',
            'ip': 'global',
            'condition': f'samples={samples}',
            'rate': mean,
            'baseline': stddev,
            'duration': 0
        })
