import threading
import time
import psutil
from flask import Flask, jsonify, render_template_string

HTML = """<!DOCTYPE html>
<html>
<head>
    <title>HNG Anomaly Detector</title>
    <style>
        body { font-family: monospace; background: #0a0a0a; color: #00ff00; padding: 20px; }
        .card { border: 1px solid #00ff00; padding: 15px; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #00ff00; padding: 8px; }
        .red { color: #ff0000; }
    </style>
    <meta http-equiv="refresh" content="3">
</head>
<body>
    <h1>HNG Anomaly Detection Dashboard</h1>
    <div class="card">
        Uptime: {{ uptime }} | Global req/s: {{ global_rate }} | CPU: {{ cpu }}% | Memory: {{ memory }}%
    </div>
    <div class="card">
        Baseline mean: {{ mean }} req/s | stddev: {{ stddev }}
    </div>
    <div class="card">
        <h3>Banned IPs</h3>
        <table>
            <tr><th>IP</th><th>Duration</th><th>Remaining</th></tr>
            {% for b in banned %}
            <tr class="red"><td>{{ b.ip }}</td><td>{{ b.duration }}s</td>
            <td>{{ "permanent" if b.remaining == -1 else (b.remaining|int|string + "s") }}</td></tr>
            {% endfor %}
        </table>
    </div>
    <div class="card">
        <h3>Top 10 IPs</h3>
        <table>
            <tr><th>IP</th><th>Requests</th></tr>
            {% for ip, count in top_ips %}
            <tr><td>{{ ip }}</td><td>{{ count }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body></html>"""

class Dashboard:
    def __init__(self, config, detector, blocker, baseline, start_time):
        self.detector = detector
        self.blocker = blocker
        self.baseline = baseline
        self.start_time = start_time
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            uptime = int(time.time() - self.start_time)
            hours, rem = divmod(uptime, 3600)
            mins, secs = divmod(rem, 60)
            return render_template_string(HTML,
                uptime=f"{hours}h {mins}m {secs}s",
                global_rate=f"{self.detector.get_global_rate():.2f}",
                cpu=psutil.cpu_percent(),
                memory=psutil.virtual_memory().percent,
                mean=f"{self.baseline.effective_mean:.2f}",
                stddev=f"{self.baseline.effective_stddev:.2f}",
                banned=self.blocker.get_banned_list(),
                top_ips=self.detector.get_top_ips()
            )

        @self.app.route("/api/metrics")
        def metrics():
            return jsonify({
                "global_rate": self.detector.get_global_rate(),
                "banned_ips": self.blocker.get_banned_list(),
                "top_ips": self.detector.get_top_ips(),
                "baseline_mean": self.baseline.effective_mean,
                "baseline_stddev": self.baseline.effective_stddev,
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent,
                "uptime": int(time.time() - self.start_time)
            })

    def start(self, port=8888):
        thread = threading.Thread(
            target=lambda: self.app.run(host="0.0.0.0", port=port, debug=False),
            daemon=True
        )
        thread.start()
