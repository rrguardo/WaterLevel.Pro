#!/bin/bash


PROCESS_NAME="sms_alerts_cron"

cd /root/wlp


# Check if the uWSGI process is running
if ! pgrep -f "PROCESS_NAME" > /dev/null; then
    # The uWSGI process is not running, so restart it
    echo "SMS alert process is not running. Safe to start now"
    ./venv/bin/python sms_alerts_cron.py
else
    echo "Warning SMS alert process is running. !INCREASE CRON MINUTES!"
fi
