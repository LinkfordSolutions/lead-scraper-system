#!/bin/bash
# Start Lead Scraper System in background

cd /root/lead-scraper-system
source venv/bin/activate
nohup python app.py > logs/app_run.log 2>&1 &

echo "Lead Scraper System started in background"
echo "PID: $!"
echo "Logs: tail -f logs/app_run.log"
