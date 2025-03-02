import asyncio
import time
from celery import Celery
from aiogram import Bot
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, select
from datetime import datetime
from config import configs
from models import TelegramUsers, TodoLists

celery = Celery("tasks", broker=configs.REDIS_BROKER, backend=configs.REDIS_BROKER)

bot = Bot(token=configs.BOT_TOKEN)

engine = create_engine(configs.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery.task
def send_reminders():
    with SessionLocal() as db:
        now = datetime.now().date()
        tasks = db.execute(
            select(TodoLists).filter(TodoLists.deadline == now, TodoLists.is_done == False)
        ).scalars().all()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for task in tasks:
            user = db.execute(
                select(TelegramUsers).filter(TelegramUsers.id == task.user_id)
            ).scalars().first()

            if user:
                message = f"🔔 Напоминание!\nЗадача: {task.todo_name}\nДедлайн: {task.deadline}"
                loop.run_until_complete(bot.send_message(user.telegram_id, message))
