from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database import upsert_user
import asyncio

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await asyncio.to_thread(
        upsert_user,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("ℹ️ Помощь"), KeyboardButton("📝 Проверить решение задачи")],
            [KeyboardButton("👥 Поддержка")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

    await update.message.reply_text(
        '''<b>👋 Здравствуйте! </b>
        
Я Ваш карманный бот-наставник RepMat, и я создан для того, чтобы помогать изучать математику, проверяя решения Ваших задач.
Для того, чтобы прочитать подробную инструкцию по работе с ботом, нажмите кнопку ℹ️ Помощь или напишите команду 
Чтобы получить ссылку на бота для обратной связи с создателем, нажмите кнопку 👥 Поддержка.
Чтобы начать проверять задачу, нажмите кнопку 📝 Проверить решение задачи.

😊 Продуктивного использования!''',
        reply_markup=keyboard, parse_mode='HTML'
    )

