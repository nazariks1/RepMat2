from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("ℹ️ Помощь"), KeyboardButton("📝 Проверить решение задачи")],
            [KeyboardButton("👥 Поддержка")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
    await update.message.reply_text(
        "❌ Задача отменена ",
        reply_markup=keyboard,
    )
    return ConversationHandler.END