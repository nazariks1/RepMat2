from telegram import Update, InputMediaPhoto, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from handlers.task import WAITING_SOLUTION, WAITING_QUESTION
from services.ocr import recognize_task_image, recognize_solution_images
from services.ai_checker import check_solution_safe, ask_question_safe
from services.renderer import render_to_images
from services.topic_extractor import extract_topics
from services.link_finder import find_theory_links
from database import log_task
import asyncio
import io

async def _send_images(update: Update, result: str, caption: str = "✅ Результат проверки"):
    try:
        pages = await asyncio.to_thread(render_to_images, result)
        if len(pages) == 1:
            await update.message.reply_photo(
                photo=io.BytesIO(pages[0]),
                caption=caption,
            )
        else:
            BATCH = 10
            for batch_start in range(0, len(pages), BATCH):
                batch = pages[batch_start:batch_start + BATCH]
                media_group = [
                    InputMediaPhoto(
                        media=io.BytesIO(png),
                        caption=caption if i == 0 and batch_start == 0 else ""
                    )
                    for i, png in enumerate(batch)
                ]
                await update.message.reply_media_group(media=media_group)
    except Exception as e:
        print(f"Ошибка: {e}")
        await update.message.reply_text(
            "Не удалось отрендерить формулы. Бот отправит текстом:\n\n"
        )
        for i in range(0, len(result), 4096):
            await update.message.reply_text(result[i:i + 4096])

async def _send_theory_links(update: Update, task_text: str, solution_text: str):
    try:
        await update.message.reply_text("🔍 Подбираются материалы по теории...")
        topics = await extract_topics(task_text, solution_text)
        if not topics:
            return
        links_by_topic = await find_theory_links(topics, links_per_topic=2)
        if not links_by_topic:
            return
        lines = ["📚 *Полезные материалы по темам задачи:*\n"]
        for topic, links in links_by_topic.items():
            lines.append(f"*{topic.capitalize()}*")
            for link in links:
                lines.append(f"• [{link['title']}]({link['url']})")
            lines.append("")
        message = "\n".join(lines).strip()
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except Exception as e:
        print(f"Ошибка: {e}")

def _question_keyboard():
    return ReplyKeyboardMarkup(
        [["❓ Задать вопрос", "🏠 В главное меню"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
def _main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("ℹ️ Помощь"), KeyboardButton("📝 Проверить решение задачи")],
            [KeyboardButton("👥 Поддержка")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

async def receive_solution_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    solution_text = update.message.text
    existing = context.user_data.get("solution_text", "")
    context.user_data["solution_text"] = (existing + "\n" + solution_text) if existing else solution_text
    await update.message.reply_text("✅ *Текст принят!* Можете добавить ещё или написать /done")
    return WAITING_SOLUTION


async def receive_solution_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()
    if "solution_photos" not in context.user_data:
        context.user_data["solution_photos"] = []
    context.user_data["solution_photos"].append(bytes(file_bytes))
    count = len(context.user_data["solution_photos"])
    await update.message.reply_text(f"*✅ Фото {count} принято!* Можете прислать ещё или написать /done, чтобы завершить. ")
    return WAITING_SOLUTION

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Изображения распознаются...")
    task_text = context.user_data.get("task", "")
    task_photo = context.user_data.get("task_photo")
    if task_photo and not task_text:
        task_text = await recognize_task_image(task_photo)
    solution_photos = context.user_data.get("solution_photos", [])
    solution_text = context.user_data.get("solution_text", "")
    if solution_photos:
        recognized = await recognize_solution_images(solution_photos)
        solution_text = recognized + ("\n" + solution_text if solution_text else "")
    if len(task_text) <= 500:
        if len(solution_text) <= 500:
            preview = f"*📋 Распознано:*\n\nЗадача:\n{task_text}\n\nРешение:\n{solution_text}"
        else:
            preview = f"*📋 Распознано:*\n\nЗадача:\n{task_text}\n\nРешение:\n{solution_text[:500]}..."
    else:
        if len(solution_text) <= 500:
            preview = f"*📋 Распознано:*\n\nЗадача:\n{task_text[:500]}...\n\nРешение:\n{solution_text}"
        else:
            preview = f"*📋 Распознано:*\n\nЗадача:\n{task_text[:500]}...\n\nРешение:\n{solution_text[:500]}..."
    await update.message.reply_text(preview)
    await update.message.reply_text(
        "⁉ *Всё верно?* Если текст с изображений распознался плохо  — отмените через /cancel.\n\n"
        "Продолжается проверка..."
    )
    result = await check_solution_safe(task_text, solution_text)
    await asyncio.to_thread(
        log_task,
        user_id=update.effective_user.id,
        task_text=task_text,
        result_text=result,
    )
    await update.message.reply_text("🖼 Формируется результат проверки в виде изображений...")
    await _send_images(update, result)
    await _send_theory_links(update, task_text, solution_text)
    context.user_data["task_text_for_qa"] = task_text
    context.user_data["solution_text_for_qa"] = solution_text
    context.user_data["check_result_for_qa"] = result
    await update.message.reply_text(
        "*Есть вопросы по решению или разбору?* Напишите их текстом - постараюсь ответить подробно 🙂\n\n",
        reply_markup=_question_keyboard(),
    )
    return WAITING_QUESTION

async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "🏠 В главное меню":
        context.user_data.clear()
        await update.message.reply_text(
            "Возвращаемся в главное меню!",
            reply_markup=_main_keyboard(),
        )
        return ConversationHandler.END
    if text == "❓ Задать вопрос":
        await update.message.reply_text(
            "Напишите свой вопрос текстом, я постараюсь объяснить подробнее:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return WAITING_QUESTION
    await update.message.reply_text("🤔 Идёт размышление над ответом...")
    task_text = context.user_data.get("task_text_for_qa", "")
    solution_text = context.user_data.get("solution_text_for_qa", "")
    check_result = context.user_data.get("check_result_for_qa", "")
    answer = await ask_question_safe(
        task=task_text,
        solution=solution_text,
        check_result=check_result,
        question=text,
    )
    await update.message.reply_text("🖼 Формируется ответ в виде изображений...")
    await _send_images(update, answer, caption="💬 Ответ на вопрос")
    await update.message.reply_text(
        "🫡 Есть ли еще у вас вопросы?",
        reply_markup=_question_keyboard(),
    )
    return WAITING_QUESTION