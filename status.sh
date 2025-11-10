#!/bin/bash
# Check Lead Scraper System Status

echo "════════════════════════════════════════════════════════════"
echo "Lead Scraper System Status"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if process is running
if pgrep -f "python.*app.py" > /dev/null; then
    PID=$(pgrep -f "python.*app.py")
    echo "✅ System is RUNNING (PID: $PID)"

    # Show process info
    echo ""
    echo "Process info:"
    ps aux | grep -E "python.*app.py" | grep -v grep

    # Show latest logs
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Latest logs (last 15 lines):"
    echo "════════════════════════════════════════════════════════════"
    tail -15 logs/app_run.log
else
    echo "❌ System is NOT running"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Commands:"
echo "  Start:  ./start_background.sh"
echo "  Stop:   ./stop.sh"
echo "  Logs:   tail -f logs/app_run.log"
echo "════════════════════════════════════════════════════════════"
