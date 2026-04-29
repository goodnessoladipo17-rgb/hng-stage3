import time
import math
from collections import deque

class BaselineTracker:
    def __init__(self, window_minutes=30, recalc_interval=60):
        self.window_minutes = window_minutes
        self.recalc_interval = recalc_interval
        self.per_second_counts = deque()
        self.hourly_slots = {}
        self.effective_mean = 1.0
        self.effective_stddev = 1.0
        self.error_mean = 0.1
        self.last_recalc = time.time()
        self.current_second_count = 0
        self.current_second = int(time.time())
        self.current_second_errors = 0

    def record_request(self, is_error=False):
        now = int(time.time())
        if now != self.current_second:
            self.per_second_counts.append({
                'ts': self.current_second,
                'count': self.current_second_count,
                'errors': self.current_second_errors
            })
            cutoff = now - (self.window_minutes * 60)
            while self.per_second_counts and self.per_second_counts[0]['ts'] < cutoff:
                self.per_second_counts.popleft()
            self.current_second = now
            self.current_second_count = 0
            self.current_second_errors = 0
        self.current_second_count += 1
        if is_error:
            self.current_second_errors += 1
        if time.time() - self.last_recalc >= self.recalc_interval:
            self.recalculate()

    def recalculate(self):
        now = time.time()
        hour_slot = int(now // 3600)
        counts = [s['count'] for s in self.per_second_counts]
        errors = [s['errors'] for s in self.per_second_counts]
        if len(counts) >= 10:
            mean = sum(counts) / len(counts)
            variance = sum((c - mean) ** 2 for c in counts) / len(counts)
            stddev = math.sqrt(variance)
            self.hourly_slots[hour_slot] = {
                'mean': max(mean, 1.0),
                'stddev': max(stddev, 0.5)
            }
            if hour_slot in self.hourly_slots and len(counts) > 60:
                self.effective_mean = self.hourly_slots[hour_slot]['mean']
                self.effective_stddev = self.hourly_slots[hour_slot]['stddev']
            else:
                self.effective_mean = max(mean, 1.0)
                self.effective_stddev = max(stddev, 0.5)
            if errors:
                self.error_mean = max(sum(errors) / len(errors), 0.1)
        self.last_recalc = now
        return {
            'effective_mean': self.effective_mean,
            'effective_stddev': self.effective_stddev,
            'error_mean': self.error_mean,
            'samples': len(counts)
        }

    def get_zscore(self, rate):
        if self.effective_stddev == 0:
            return 0
        return (rate - self.effective_mean) / self.effective_stddev
