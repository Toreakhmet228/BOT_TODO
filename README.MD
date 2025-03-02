# Telegram Task Manager Bot

Этот проект представляет собой Telegram-бота для управления задачами с интеграцией Celery и базы данных PostgreSQL.

## Функционал
- Регистрация пользователей
- Добавление, просмотр и завершение задач
- Хранение данных в PostgreSQL
- Фоновые уведомления через Celery и Redis

## Требования
- Docker и Docker Compose
- Python 3.9+
- PostgreSQL
- Redis
- Телеграм-бот с полученным токеном

## Установка и запуск

1. **Создайте `.env` файл** в корневой директории и укажите переменные окружения:

   ```env
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=your_db
   BOT_TOKEN=your_telegram_bot_token
   ```

2. **Соберите и запустите контейнеры**:

   ```sh
   docker-compose up --build -d
   ```

3. **Проверка логов**:

   ```sh
   docker-compose logs -f
   ```

## Структура проекта
```
.
├── config.py          # Конфигурационный файл
├── db.py              # Настройка базы данных
├── docker-compose.yml # Конфигурация Docker Compose
├── Dockerfile         # Docker-образ для бота
├── env                # Файл переменных окружения (необходимо создать)
├── main.py            # Основной код бота
├── models.py          # SQLAlchemy-модели
├── requirements.txt   # Зависимости проекта
├── tasks.py           # Фоновые задачи Celery
└── README.md          # Описание проекта
```

## Использование
Запустите бота в Telegram и введите команду `/start`, чтобы начать работу.

## Разработка
Для локального тестирования без Docker установите зависимости и запустите бота вручную:

```sh
pip install -r requirements.txt
python main.py
```

Запуск Celery в отдельном терминале:

```sh
celery -A tasks worker --loglevel=info
```

## Лицензия
MIT License.

