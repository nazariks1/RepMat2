from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes


async def task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✏️ Отправьте условие задачи — текстом или фото.\n\n",
        reply_markup=ReplyKeyboardRemove(),
    )