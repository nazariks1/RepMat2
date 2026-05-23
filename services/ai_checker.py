import httpx
from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TEXT_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-4-maverick:free",
    "deepseek/deepseek-r1:free",
    "mistralai/mistral-7b-instruct:free",
]

async def _call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://math-bot",
        "X-Title": "MathBot",
    }
    last_error = None
    async with httpx.AsyncClient(timeout=90) as client:
        for model in TEXT_MODELS:
            try:
                body = {
                    "model": model,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000,
                }
                resp = await client.post(OPENROUTER_URL, headers=headers, json=body)
                if resp.status_code != 200:
                    print(f"Ошибка: {resp.text[:300]}")
                    last_error = f"HTTP {resp.status_code}"
                    continue
                data = resp.json()
                if "error" in data:
                    last_error = str(data["error"])
                    continue
                content = data["choices"][0]["message"]["content"]
                used_model = data.get("model", model)
                return content
            except Exception as e:
                print(f"Ошибка {type(e).__name__}: {e}")
                last_error = str(e)
    return f"Не удалось получить ответ от AI. Ошибка: {last_error}"

async def check_solution(task: str, solution: str) -> str:
    prompt = f"""Ты - опытный учитель математики, проводишь индивидуальное занятие с учеником.
    Ученик предоставил тебе условие задачи {task} и его решение {solution} для проверки.
    Перед тем как писать ответ, мысленно пройди по каждому шагу решения ученика от начала до конца несколько раз. Только после этого пиши финальный ответ.
    - Если ты написал, что шаг неверен - не пиши потом, что он верен. И наоборот.
    - Каждый шаг оценивается ровно один раз - либо верно, либо неверно.
    - Не противоречь сам себе ни в одном месте ответа.
    - Не придирайся без повода: если логика и результат верны - шаг верный, даже если оформление отличается.
    - Учитывай контекст программы по математике Республики Беларусь.
    - У задачи может быть несколько правильных способов решения - проверяй логику и правильность переходов, а не соответствие конкретному методу.
    - Твоя цель - не найти как можно больше ошибок, а определить, правилен ли ответ и правильно ли в целом решение.
    - В своем ответе освещай только ошибки, которые грубы и создают неправильность решения.
    План ответа:
    1. Проверка решения
    Пройди по шагам решения ученика. Для каждой грубой найденной ошибки или весомой неточности укажи:
       - что именно неверно
       - почему это ошибка
       - как надо было сделать правильно
    Если ошибок нет - напиши: «Решение верное!»
    Ты должен писать чётко и по делу.
    2. Правильное
    Предлагай правильное решение, только если исходное содержит несколько значительных ошибок
    Дай полное решение с пояснением каждого шага. Пиши понятно и доступно, но строго и логично.
    Отвечай на русском языке. Будь конкретным и доброжелательным."""
    return await _call_llm(prompt)

async def ask_question(task: str, solution: str, check_result: str, question: str) -> str:
    prompt = f"""Ты - опытный учитель математики, проводишь индивидуальное занятие с учеником.
    Ранее ченик предоставил тебе условие задачи {task} и его решение {solution} для проверки.
    Ты уже дал результат проверки ученику {check_result}.
    Теперь ученик задаёт дополнительный вопрос: {question}
Ответь на вопрос подробно и понятно, опираясь на контекст задачи и разбора выше.
Если вопрос касается конкретного шага - объясни этот шаг развёрнуто.
Отвечай на русском языке. Будь доброжелательным и терпеливым."""
    return await _call_llm(prompt)

async def check_solution_safe(task: str, solution: str) -> str:
    if not task or not solution:
        return (
            "<b>Не хватает данных для проверки.</b>\n\n"
            "Убедитесь, что отправили:\n"
            "1. Условие задачи\n"
            "2. Ваше решение\n\n"
            "Можете отправить текстом, это надёжнее чем фото."
        )
    if "[Не удалось" in task or "[Не распознано]" in solution:
        return (
            f'''<b>OCR не смог распознать изображения.</b> Попробуйте еще раз.
            
 <b>📷 Рекомендации по работе с фотографиями</b>
1. Старайтесь писать на таком материале, на котором написанный текст не будет сливаться с фоном, например, с клеточками тетрадного листа.
2. Пишите настолько разборчиво, насколько это возможно. Придерживайтесь крупного почерка.
3. Делайте фотографии при хорошем освещении.
4. Отправляйте изображения в таком положении, чтобы текст легко считался сверху вниз.'''
        )
    return await check_solution(task, solution)

async def ask_question_safe(task: str, solution: str, check_result: str, question: str) -> str:
    if not question.strip():
        return "Вопрос не содержит текста. Попробуйте еще раз."
    return await ask_question(task, solution, check_result, question)