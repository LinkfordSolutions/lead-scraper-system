# Deployment Guide - Lead Scraper System

Руководство по развертыванию системы в production.

---

## 🐳 Docker Deployment (Рекомендуется)

### Предварительные требования

- Docker 20.10+
- Docker Compose 1.29+

### Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/LinkfordSolutions/lead-scraper-system.git
cd lead-scraper-system

# 2. Настроить переменные окружения
cp .env.example .env
nano .env  # Отредактировать .env

# 3. Запустить систему
docker-compose up -d

# 4. Проверить статус
docker-compose ps
docker-compose logs -f app

# 5. Инициализировать базу данных (только при первом запуске)
docker-compose exec app python init_db.py
```

### Управление

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart app

# Логи
docker-compose logs -f app

# Health check
docker-compose exec app python health_check.py

# Обновление
git pull origin main
docker-compose build app
docker-compose up -d
```

### Volumes

Docker Compose создает следующие volumes:

- `postgres_data` - данные PostgreSQL
- `./logs` - логи приложения
- `./data` - экспортированные CSV/Excel файлы

---

## 🔧 Systemd Service (Native)

Для запуска системы как systemd сервис (без Docker).

### Установка

```bash
# 1. Скопировать service файл
sudo cp lead-scraper.service /etc/systemd/system/

# 2. Перезагрузить systemd
sudo systemctl daemon-reload

# 3. Включить автозапуск
sudo systemctl enable lead-scraper

# 4. Запустить сервис
sudo systemctl start lead-scraper

# 5. Проверить статус
sudo systemctl status lead-scraper
```

### Управление

```bash
# Старт
sudo systemctl start lead-scraper

# Стоп
sudo systemctl stop lead-scraper

# Перезапуск
sudo systemctl restart lead-scraper

# Статус
sudo systemctl status lead-scraper

# Логи
sudo journalctl -u lead-scraper -f

# Логи с последнего запуска
sudo journalctl -u lead-scraper --since today
```

### Просмотр логов

Логи systemd доступны в:
- `/root/lead-scraper-system/logs/systemd.log` - stdout
- `/root/lead-scraper-system/logs/systemd-error.log` - stderr

---

## 🏥 Мониторинг и Health Checks

### Health Check Script

```bash
# Ручная проверка
python health_check.py

# В Docker
docker-compose exec app python health_check.py
```

Проверяемые компоненты:
- ✅ Подключение к БД
- ✅ Процесс приложения
- ✅ Telegram bot token
- ✅ Свежесть логов

### Автоматический мониторинг (Cron)

```bash
# Добавить в crontab
crontab -e

# Проверка каждые 5 минут
*/5 * * * * cd /root/lead-scraper-system && ./venv/bin/python health_check.py >> logs/health.log 2>&1

# Отправка уведомлений при ошибках
*/5 * * * * cd /root/lead-scraper-system && ./venv/bin/python health_check.py || echo "Lead Scraper is DOWN!" | mail -s "Alert" admin@example.com
```

---

## 📝 Логи

### Расположение логов

- `logs/app.log` - основной лог приложения
- `logs/app_run.log` - лог при запуске через start_background.sh
- `logs/bot.log` - лог Telegram бота
- `logs/systemd.log` - systemd stdout
- `logs/systemd-error.log` - systemd stderr
- `logs/health.log` - health check логи

### Ротация логов

Создать `/etc/logrotate.d/lead-scraper`:

```
/root/lead-scraper-system/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

Применить:
```bash
sudo logrotate -f /etc/logrotate.d/lead-scraper
```

---

## 🔐 Безопасность

### Firewall

```bash
# Разрешить только локальный доступ к PostgreSQL
sudo ufw allow from 127.0.0.1 to any port 5432

# Если используется Docker
sudo ufw allow from 172.16.0.0/12 to any port 5432
```

### Секреты

❗ **ВАЖНО**: Никогда не коммитить .env в Git!

```bash
# Проверить, что .env в .gitignore
cat .gitignore | grep .env

# Установить правильные права
chmod 600 .env
```

### Обновление зависимостей

```bash
# Проверить устаревшие пакеты
pip list --outdated

# Обновить requirements.txt
pip freeze > requirements.txt

# При использовании Docker пересобрать образ
docker-compose build app
```

---

## 🔄 Backup и Restore

### Backup базы данных

```bash
# Создать backup
docker-compose exec postgres pg_dump -U lead_scraper lead_scraper_db > backup_$(date +%Y%m%d).sql

# Или через pg_dump напрямую
pg_dump -h localhost -U lead_scraper -d lead_scraper_db > backup_$(date +%Y%m%d).sql
```

### Restore базы данных

```bash
# Восстановить из backup
docker-compose exec -T postgres psql -U lead_scraper lead_scraper_db < backup_20231210.sql

# Или через psql
psql -h localhost -U lead_scraper -d lead_scraper_db < backup_20231210.sql
```

### Автоматический backup (Cron)

```bash
# Добавить в crontab
0 2 * * * docker-compose -f /root/lead-scraper-system/docker-compose.yml exec -T postgres pg_dump -U lead_scraper lead_scraper_db | gzip > /backups/leadscr_$(date +\%Y\%m\%d).sql.gz
```

---

## 🚀 Production Tips

### 1. Переменные окружения

Обязательные для production:
```bash
LOG_LEVEL=WARNING  # Уменьшить verbosity
TELEGRAM_BOT_TOKEN=<real_token>
BOT_PASSWORD=<strong_password>
DB_PASSWORD=<strong_password>
```

### 2. Resource Limits (Docker)

Добавить в `docker-compose.yml`:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 3. Reverse Proxy (опционально)

Если нужен web интерфейс, добавить nginx:
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

### 4. Мониторинг

Рекомендуемые инструменты:
- **Uptime monitoring**: UptimeRobot, Pingdom
- **Log aggregation**: ELK Stack, Loki
- **Metrics**: Prometheus + Grafana (если нужно)

---

## 🐛 Troubleshooting

### Проблема: Бот не отвечает

```bash
# 1. Проверить процесс
docker-compose ps
# или
sudo systemctl status lead-scraper

# 2. Проверить логи
docker-compose logs app | tail -50

# 3. Проверить token
echo $TELEGRAM_BOT_TOKEN

# 4. Перезапустить
docker-compose restart app
```

### Проблема: База данных недоступна

```bash
# 1. Проверить подключение
docker-compose exec postgres psql -U lead_scraper -d lead_scraper_db -c "SELECT 1"

# 2. Проверить логи PostgreSQL
docker-compose logs postgres

# 3. Перезапустить PostgreSQL
docker-compose restart postgres
```

### Проблема: Парсеры не работают

```bash
# 1. Проверить API ключи
grep API_KEY .env

# 2. Проверить логи парсеров
docker-compose logs app | grep parser

# 3. Запустить тест парсеров
docker-compose exec app python test_parsers_quick.py
```

---

## 📞 Поддержка

При возникновении проблем:

1. Проверить логи: `docker-compose logs app`
2. Запустить health check: `python health_check.py`
3. Создать issue: https://github.com/LinkfordSolutions/lead-scraper-system/issues

---

**Last updated**: 2025-11-10
