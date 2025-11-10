#!/usr/bin/env python
"""
Health check script for Lead Scraper System
"""
import sys
import os
import psycopg2
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from src.utils.config import config


def check_database():
    """Check database connectivity"""
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            connect_timeout=5
        )
        conn.close()
        return True, "Database OK"
    except Exception as e:
        return False, f"Database ERROR: {e}"


def check_process():
    """Check if main process is running"""
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'app.py' in cmdline:
                    return True, f"Process OK (PID: {proc.info['pid']})"
        return False, "Process NOT RUNNING"
    except ImportError:
        # psutil not installed, skip this check
        return True, "Process check skipped (psutil not available)"
    except Exception as e:
        return False, f"Process check ERROR: {e}"


def check_bot_token():
    """Check if bot token is configured"""
    try:
        if config.TELEGRAM_BOT_TOKEN and len(config.TELEGRAM_BOT_TOKEN) > 20:
            return True, "Bot token OK"
        return False, "Bot token NOT configured"
    except Exception as e:
        return False, f"Bot token ERROR: {e}"


def check_logs():
    """Check if logs are being written"""
    try:
        # Check both log files
        log_files = ['logs/app.log', 'logs/app_run.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                mtime = os.path.getmtime(log_file)
                age = datetime.now().timestamp() - mtime
                if age < 300:  # Less than 5 minutes old
                    return True, f"Logs OK (updated {int(age)}s ago)"

        # If we get here, check if any log file exists but is stale
        for log_file in log_files:
            if os.path.exists(log_file):
                mtime = os.path.getmtime(log_file)
                age = datetime.now().timestamp() - mtime
                return False, f"Logs STALE ({int(age)}s old)"

        return False, "Log files NOT FOUND"
    except Exception as e:
        return False, f"Logs ERROR: {e}"


def main():
    """Run all health checks"""
    print("="*60)
    print("Lead Scraper System - Health Check")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    checks = [
        ("Database Connection", check_database),
        ("Main Process", check_process),
        ("Bot Token", check_bot_token),
        ("Log Files", check_logs)
    ]

    all_passed = True
    for name, check_func in checks:
        success, message = check_func()
        status = "✅" if success else "❌"
        print(f"{status} {name:20} - {message}")
        if not success:
            all_passed = False

    print()
    print("="*60)

    if all_passed:
        print("Status: HEALTHY ✅")
        print("="*60)
        sys.exit(0)
    else:
        print("Status: UNHEALTHY ❌")
        print("="*60)
        sys.exit(1)


if __name__ == '__main__':
    main()
