# Telegram Bot Testing Guide

## Bot Information

- **Bot Username**: @TargetLink_lead_bot
- **Bot Token**: `8231414810:AAHR9_janZFOA7LJJ_cDkMEXPB9M37uDVxc`
- **Authorization Password**: `qcW5be4mczNVFs3v`

## Starting the Bot

### Method 1: Direct Python
```bash
cd /root/lead-scraper-system
source venv/bin/activate
python -m src.bot.bot
```

### Method 2: Shell Script
```bash
cd /root/lead-scraper-system
./run_bot.sh
```

### Method 3: Background Process
```bash
cd /root/lead-scraper-system
./run_bot.sh > logs/bot_run.log 2>&1 &
```

## Testing the Bot

### 1. Find the Bot
Open Telegram and search for: **@TargetLink_lead_bot**

### 2. Test /start Command
Send: `/start`

Expected response:
- Welcome message
- Instructions to use `/auth` command

### 3. Test Authorization
Send: `/auth qcW5be4mczNVFs3v`

Expected response:
- Success message
- List of available commands

### 4. Test Unauthorized Access
Before authorization, try: `/get_leads`

Expected response:
- Access denied message

### 5. Test /get_leads Command
After authorization, send: `/get_leads`

Expected response:
- "Generating file..." message
- CSV file with 10 test companies
- Statistics message with breakdown by category

### 6. Test /status Command
Send: `/status`

Expected response:
- "No scraping sessions yet" message (if no scraping has run)

### 7. Test /help Command
Send: `/help`

Expected response:
- List of all commands
- Target niches
- Geographic scope
- Update schedule

## Test Data

The database contains 10 test companies:
1. AutoService Premium (СТО) - Минск
2. Мастер на час "Умелые руки" - Минск
3. Клининг "Чистый дом" - Гомель
4. Грузоперевозки "Быстрый переезд" - Брест
5. Репетиторский центр "Знание" - Гродно
6. Фитнес-клуб "Энергия" - Витебск
7. Фотостудия "Момент" - Могилев
8. Юридическая компания "Правовед" - Минск
9. Психологический центр "Гармония" - Минск
10. Тату-салон "Ink Masters" - Минск

## Expected CSV Format

The exported CSV should contain the following columns:
- Название
- Категория
- Адрес
- Город
- Район
- Телефон
- Email
- Сайт
- Instagram
- Facebook
- VK
- Telegram
- Рейтинг
- Отзывов
- Широта
- Долгота
- Источник
- Дата обновления

## Troubleshooting

### Bot doesn't respond
1. Check if bot is running: `ps aux | grep bot.py`
2. Check logs: `cat logs/bot.log`
3. Verify token in `.env` file

### Authorization fails
1. Check password in `.env`: `BOT_PASSWORD`
2. Verify database connection
3. Check user table: `psql -U lead_scraper -d lead_scraper_db -c "SELECT * FROM bot_users;"`

### CSV export fails
1. Check if companies exist: `psql -U lead_scraper -d lead_scraper_db -c "SELECT COUNT(*) FROM companies;"`
2. Verify data directory exists: `ls -la data/`
3. Check logs for errors

### Database connection issues
1. Check PostgreSQL is running: `systemctl status postgresql`
2. Verify credentials in `.env`
3. Test connection: `psql -U lead_scraper -d lead_scraper_db -c "SELECT 1;"`

## Logs

- **Bot logs**: `logs/bot.log`
- **Application logs**: `logs/scraper.log`
- **Run logs**: `logs/bot_run.log` (if started in background)

## Security Notes

- Never share the bot token publicly
- Keep the authorization password secure
- Regularly review authorized users in database
- Monitor bot logs for suspicious activity
