import json
import time
import os

def tail_log(filepath):
    """Continuously tail a log file and yield new lines."""
    while not os.path.exists(filepath):
        print(f"Waiting for log file: {filepath}")
        time.sleep(2)
    
    with open(filepath, 'r') as f:
        f.seek(0, 2)  # Seek to end
        while True:
            line = f.readline()
            if line:
                line = line.strip()
                if line:
                    yield line
            else:
                time.sleep(0.1)

def parse_line(line):
    """Parse a JSON log line into a dict."""
    try:
        data = json.loads(line)
        ip = data.get('source_ip', '-')
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        return {
            'ip': ip,
            'timestamp': data.get('timestamp', ''),
            'method': data.get('method', ''),
            'path': data.get('path', ''),
            'status': int(data.get('status', 0)),
            'response_size': int(data.get('response_size', 0)),
        }
    except Exception:
        return None
