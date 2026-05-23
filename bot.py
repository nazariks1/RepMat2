import sys
from telegram import ReplyKeyboardMarkup, KeyboardButton
from handlers.cancel import cancel
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ConversationHandler, MessageHandler,
    filters
)
from config import BOT_TOKEN
from handlers.start import start
from handlers.help import help_command
from handlers.task_start import task_start
from handlers.task import receive_task_text, receive_task_photo, WAITING_SOLUTION, WAITING_QUESTION
from handlers.solution import receive_solution_photo, receive_solution_text, done, receive_question
from database import init_db

async def support(update, context):
    await update.message.reply_text(
        "По любым вопросам обращайтесь: @repmatqa_bot"
    )

def main():
    try:
        init_db()
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^📝 Проверить решение задачи$"), task_start),
                CommandHandler("task", task_start),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND
                    & ~filters.Regex("^(ℹ️ Помощь|📝 Проверить решение задачи|👥 Поддержка)$"),
                    receive_task_text
                ),
                MessageHandler(filters.PHOTO, receive_task_photo),
            ],
            states={
                WAITING_SOLUTION: [
                    MessageHandler(filters.PHOTO, receive_solution_photo),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_solution_text),
                    CommandHandler("done", done),
                ],
                WAITING_QUESTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question),
                ],
            },
            fallbacks=[
                CommandHandler("start", start),
                CommandHandler("cancel", cancel),
            ],
        )
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.Regex("^ℹ️ Помощь$"), help_command))
        app.add_handler(MessageHandler(filters.Regex("^👥 Поддержка$"), support))
        app.add_handler(conv_handler)
        app.run_polling(allowed_updates=["message", "callback_query"])
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()