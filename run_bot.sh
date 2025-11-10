#!/bin/bash
# Start the Telegram bot

cd /root/lead-scraper-system
source venv/bin/activate
python -m src.bot.bot
