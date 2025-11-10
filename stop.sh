#!/bin/bash
# Stop Lead Scraper System

echo "Stopping Lead Scraper System..."

# Kill bot processes
pkill -f "python.*bot.py" 2>/dev/null
pkill -f "python.*app.py" 2>/dev/null
pkill -f "python.*bot.bot" 2>/dev/null

echo "✅ Stopped"
