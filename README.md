# HNG Stage 3 - Anomaly Detection Engine

## Overview
A real-time HTTP traffic anomaly detection daemon built alongside Nextcloud.

## Server Details
- **Server IP:** 13.53.37.195
- **Dashboard URL:** http://13.53.37.195:8080
- **Nextcloud:** http://13.53.37.195

## Language
Python - chosen for rapid development and rich standard library.

## How the Sliding Window Works
Two deque-based windows track requests over the last 60 seconds.
Each request timestamp is appended to the deque. On every check,
timestamps older than 60 seconds are evicted from the left.
Rate = len(deque) / window_seconds.

## How the Baseline Works
A rolling 30-minute window of per-second counts is maintained.
Every 60 seconds, mean and stddev are recalculated from the window.
Per-hour slots store baselines. The current hour's baseline is
preferred when it has enough data (>60 samples).
Floor values: mean=1.0, stddev=0.5 to avoid false positives.

## Detection Logic
An IP is flagged if:
- Z-score > 3.0: (rate - mean) / stddev > 3.0
- Rate > 5x baseline mean
- If error rate is 3x baseline error rate, threshold tightens to 2.1

## Blocking with iptables
When an IP is flagged:
1. iptables DROP rule added: iptables -I INPUT -s IP -j DROP
2. Slack alert sent within 10 seconds
3. Auto-unban scheduled: 10min -> 30min -> 2hr -> permanent

## Setup Instructions
```bash
git clone https://github.com/goodnessoladipo17-rgb/hng-stage3
cd hng-stage3
# Add your Slack webhook to detector/config.yaml
sudo docker-compose up -d --build
```

## Repository
https://github.com/goodnessoladipo17-rgb/hng-stage3
## Blog Post
https://dev.to/goodnessoladipo17rgb/how-i-built-a-real-time-ddos-detection-engine-for-nextcloud-h71

## Blog Post
https://dev.to/goodnessoladipo17rgb/how-i-built-a-real-time-ddos-detection-engine-for-nextcloud-h71
