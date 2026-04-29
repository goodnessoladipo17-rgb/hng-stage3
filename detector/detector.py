import time
from collections import deque, defaultdict

class AnomalyDetector:
    def __init__(self, config, baseline):
        self.config = config
        self.baseline = baseline
        self.window_seconds = config['detection']['window_seconds']
        self.zscore_threshold = config['detection']['zscore_threshold']
        self.rate_multiplier = config['detection']['rate_multiplier']
        self.error_rate_multiplier = config['detection']['error_rate_multiplier']
        # Per-IP sliding windows
        self.ip_windows = defaultdict(deque)
        self.ip_error_windows = defaultdict(deque)
        # Global sliding window
        self.global_window = deque()

    def _evict_old(self, window, now):
        cutoff = now - self.window_seconds
        while window and window[0] < cutoff:
            window.popleft()

    def record(self, ip, is_error=False):
        now = time.time()
        self.ip_windows[ip].append(now)
        self.global_window.append(now)
        if is_error:
            self.ip_error_windows[ip].append(now)
        self._evict_old(self.ip_windows[ip], now)
        self._evict_old(self.global_window, now)
        self._evict_old(self.ip_error_windows[ip], now)

    def get_ip_rate(self, ip):
        now = time.time()
        self._evict_old(self.ip_windows[ip], now)
        return len(self.ip_windows[ip]) / self.window_seconds

    def get_global_rate(self):
        now = time.time()
        self._evict_old(self.global_window, now)
        return len(self.global_window) / self.window_seconds

    def get_ip_error_rate(self, ip):
        now = time.time()
        self._evict_old(self.ip_error_windows[ip], now)
        return len(self.ip_error_windows[ip]) / self.window_seconds

    def check_ip(self, ip):
        rate = self.get_ip_rate(ip)
        zscore = self.baseline.get_zscore(rate)
        error_rate = self.get_ip_error_rate(ip)
        threshold = self.zscore_threshold
        # Tighten threshold if high error rate
        if error_rate > self.baseline.error_mean * self.error_rate_multiplier:
            threshold = self.zscore_threshold * 0.7
        if zscore > threshold:
            return True, f"zscore={zscore:.2f}", rate
        if self.baseline.effective_mean > 0 and rate > self.baseline.effective_mean * self.rate_multiplier:
            return True, f"rate={rate:.2f} > {self.rate_multiplier}x baseline", rate
        return False, None, rate

    def check_global(self):
        rate = self.get_global_rate()
        zscore = self.baseline.get_zscore(rate)
        if zscore > self.zscore_threshold:
            return True, f"global zscore={zscore:.2f}", rate
        if self.baseline.effective_mean > 0 and rate > self.baseline.effective_mean * self.rate_multiplier:
            return True, f"global rate={rate:.2f} > {self.rate_multiplier}x baseline", rate
        return False, None, rate

    def get_top_ips(self, n=10):
        now = time.time()
        rates = {}
        for ip in list(self.ip_windows.keys()):
            self._evict_old(self.ip_windows[ip], now)
            rates[ip] = len(self.ip_windows[ip])
        return sorted(rates.items(), key=lambda x: x[1], reverse=True)[:n]
