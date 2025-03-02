import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from db import get_db, Base, engine
from models import TelegramUsers, TodoLists
from config import configs
from tasks import send_reminders  # Импорт задачи Celery

logging.basicConfig(level=logging.INFO)

bot = Bot(token=configs.BOT_TOKEN)
dp = Dispatcher()

Base.metadata.create_all(bind=engine)

class TaskState(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои задачи", callback_data="tasks"),
         InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")],
        [InlineKeyboardButton(text="✅ Завершить задачу", callback_data="complete_task")],
        [InlineKeyboardButton(text="📜 Все команды", callback_data="all_commands")]
    ])

@dp.message(Command("start"))
async def start_command(message: Message):
    with next(get_db()) as db:
        user = db.execute(select(TelegramUsers).filter(TelegramUsers.telegram_id == message.from_user.id)).scalars().first()
        if not user:
            new_user = TelegramUsers(telegram_id=message.from_user.id, telegram_username=message.from_user.username)
            db.add(new_user)
            db.commit()
    await message.answer("Привет! Я помогу тебе управлять задачами.", reply_markup=main_menu())

@dp.callback_query(F.data == "all_commands")
async def all_commands(callback: CallbackQuery):
    await callback.message.answer("Доступные команды:\n/start - Запуск бота\n📋 Мои задачи - Показать список задач\n➕ Добавить задачу - Добавить новую задачу\n✅ Завершить задачу - Отметить задачу как выполненную")

@dp.callback_query(F.data == "tasks")
async def show_tasks(callback: CallbackQuery):
    with next(get_db()) as db:
        user = db.execute(select(TelegramUsers).filter(TelegramUsers.telegram_id == callback.from_user.id)).scalars().first()
        if not user:
            await callback.message.answer("Сначала отправь команду /start.")
            return
        tasks = db.execute(select(TodoLists).filter(TodoLists.user_id == user.id, TodoLists.is_done == False)).scalars().all()
        tasks_text = "\n".join([f"- {task.todo_name}" for task in tasks]) if tasks else "У тебя нет активных задач."
    await callback.message.answer(f"📋 Твои задачи:\n{tasks_text}")

@dp.callback_query(F.data == "add_task")
async def add_task(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введи название задачи:")
    await state.set_state(TaskState.waiting_for_name)

@dp.message(TaskState.waiting_for_name)
async def process_task_name(message: Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer("📝 Введи описание задачи (или напиши '-' для пропуска):")
    await state.set_state(TaskState.waiting_for_description)

@dp.message(TaskState.waiting_for_description)
async def process_task_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text if message.text != '-' else None)
    await message.answer("📅 Введи дедлайн в формате ГГГГ-ММ-ДД (или '-' для пропуска):")
    await state.set_state(TaskState.waiting_for_deadline)

@dp.message(TaskState.waiting_for_deadline)
async def process_task_deadline(message: Message, state: FSMContext):
    deadline = None
    if message.text != '-':
        try:
            deadline = datetime.strptime(message.text, "%Y-%m-%d").date()
        except ValueError:
            await message.answer("⚠️ Неверный формат! Введи дату в формате ГГГГ-ММ-ДД.")
            return

    with next(get_db()) as db:
        user = db.execute(select(TelegramUsers).filter(TelegramUsers.telegram_id == message.from_user.id)).scalars().first()
        if not user:
            await message.answer("Сначала отправь команду /start.")
            return

        data = await state.get_data()
        new_task = TodoLists(
            user_id=user.id,
            todo_name=data['task_name'],
            description=data['description'],
            deadline=deadline,
            is_done=False
        )
        db.add(new_task)
        db.commit()

    await message.answer(f"✅ Задача '{data['task_name']}' добавлена!")
    await state.clear()
@dp.callback_query(F.data == "complete_task")
async def complete_task(callback: CallbackQuery):
    with next(get_db()) as db:
        user = db.execute(select(TelegramUsers).filter(TelegramUsers.telegram_id == callback.from_user.id)).scalars().first()
        if not user:
            await callback.message.answer("Сначала отправь команду /start.")
            return

        tasks = db.execute(select(TodoLists).filter(TodoLists.user_id == user.id, TodoLists.is_done == False)).scalars().all()
        if not tasks:
            await callback.message.answer("У тебя нет активных задач для завершения.")
            return

        # Клавиатура с выбором задачи
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=task.todo_name, callback_data=f"complete_{task.id}")]
                for task in tasks
            ]
        )
        await callback.message.answer("Выбери задачу для завершения:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("complete_"))
async def confirm_complete_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    with next(get_db()) as db:
        task = db.execute(select(TodoLists).filter(TodoLists.id == task_id)).scalars().first()
        if task:
            task.is_done = True
            db.commit()
            await callback.message.answer(f"✅ Задача '{task.todo_name}' завершена!")
        else:
            await callback.message.answer("❌ Ошибка: задача не найдена.")

async def main():
    logging.info("Бот запущен")

    # Запускаем Celery задачу раз в час
    asyncio.create_task(start_celery_reminders())

    await dp.start_polling(bot)

async def start_celery_reminders():
    while True:
        send_reminders.delay()
        await asyncio.sleep(3600)
if __name__ == "__main__":
    asyncio.run(main())

