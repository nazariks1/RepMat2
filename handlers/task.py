from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

WAITING_TASK = 1
WAITING_SOLUTION = 2
WAITING_QUESTION = 3

async def receive_task_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_text = update.message.text
    context.user_data["task"] = task_text
    await update.message.reply_text(
        f'''<b>✅ Задача принята:</b>\n{task_text}**\n\n
        Теперь пришлите своё решение текстом или фото (можно несколько фото).
        Когда Вы закончите присылать фото, напишите /done. 
        
<b> 📷 Рекомендации по работе с фотографиями </b>
1. Старайтесь писать на таком материале, на котором написанный текст не будет сливаться с фоном, например, с клеточками тетрадного листа.
2. Пишите настолько разборчиво, насколько это возможно. Придерживайтесь крупного почерка.
3. Делайте фотографии при хорошем освещении.
4. Отправляйте изображения в таком положении, чтобы текст легко считался сверху вниз.'''
    ,parse_mode='HTML')
    context.user_data["solution_photos"] = []
    return WAITING_SOLUTION

async def receive_task_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()
    context.user_data["task_photo"] = bytes(file_bytes)
    await update.message.reply_text(
        '''<b>✅ Фото с задачей принято! </b> Теперь пришлите своё решение текстом или фото (можно несколько фото). 
        
Когда Вы закончите присылать фото, напишите /done. 

<b> 📷 Рекомендации по работе с фотографиями </b>
1. Старайтесь писать на таком материале, на котором написанный текст не будет сливаться с фоном, например, с клеточками тетрадного листа.
2. Пишите настолько разборчиво, насколько это возможно. Придерживайтесь крупного почерка.
3. Делайте фотографии при хорошем освещении.
4. Отправляйте изображения в таком положении, чтобы текст легко считался сверху вниз.'''
    ,parse_mode='HTML')
    context.user_data["solution_photos"] = []
    return WAITING_SOLUTION