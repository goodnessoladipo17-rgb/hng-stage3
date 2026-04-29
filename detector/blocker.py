import subprocess
import time

class Blocker:
    def __init__(self, config):
        self.ban_durations = config['blocking']['ban_durations']
        self.banned_ips = {}  # ip -> {banned_at, duration_index, expires_at}

    def ban(self, ip):
        if ip in self.banned_ips:
            idx = min(self.banned_ips[ip]['duration_index'] + 1, len(self.ban_durations) - 1)
        else:
            idx = 0
        duration = self.ban_durations[idx]
        expires_at = time.time() + duration if duration > 0 else -1
        self.banned_ips[ip] = {
            'banned_at': time.time(),
            'duration_index': idx,
            'duration': duration,
            'expires_at': expires_at
        }
        try:
            subprocess.run(
                ['iptables', '-I', 'INPUT', '-s', ip, '-j', 'DROP'],
                check=True, capture_output=True
            )
        except Exception as e:
            print(f"iptables error: {e}")
        return duration

    def unban(self, ip):
        try:
            subprocess.run(
                ['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'],
                check=True, capture_output=True
            )
        except Exception as e:
            print(f"iptables unban error: {e}")
        if ip in self.banned_ips:
            del self.banned_ips[ip]

    def is_banned(self, ip):
        return ip in self.banned_ips

    def check_expired_bans(self):
        now = time.time()
        expired = []
        for ip, info in list(self.banned_ips.items()):
            if info['expires_at'] != -1 and now >= info['expires_at']:
                expired.append(ip)
        return expired

    def get_banned_list(self):
        now = time.time()
        result = []
        for ip, info in self.banned_ips.items():
            remaining = info['expires_at'] - now if info['expires_at'] != -1 else -1
            result.append({
                'ip': ip,
                'banned_at': info['banned_at'],
                'duration': info['duration'],
                'remaining': remaining
            })
        return result
