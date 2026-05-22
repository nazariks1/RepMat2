import json
import httpx
from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TEXT_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-4-maverick:free",
    "deepseek/deepseek-r1:free",
    "mistralai/mistral-7b-instruct:free",
]
_PROMPT_TEMPLATE = """Ты - опытный учитель математики, проводишь индивидуальное занятие с учеником.
Ученик предоставил тебе условие задачи {task} и его решение {solution} для проверки.
Выдели 2-4 ключевые математические темы, которые нужно знать для решения этой задачи.
Каждая тема должна быть конкретным поисковым запросом на русском языке,
пригодным для поиска обучающей статьи (например: «квадратные уравнения», «теорема Виета», «логарифмы свойства»).
Отвечай ТОЛЬКО валидным JSON-массивом строк, без пояснений и markdown-блоков.
Пример ответа: ["квадратные уравнения", "дискриминант", "теорема Виета"]"""

async def extract_topics(task: str, solution: str) -> list[str]:
    if not OPENROUTER_API_KEY:
        return []
    prompt = _PROMPT_TEMPLATE.format(
        task=task[:1500],
        solution=solution[:1500],
    )
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://math-bot",
        "X-Title": "MathBot",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        for model in TEXT_MODELS:
            try:
                body = {
                    "model": model,
                    "temperature": 0.0,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                }
                resp = await client.post(OPENROUTER_URL, headers=headers, json=body)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                if "error" in data or not data.get("choices"):
                    continue
                raw = data["choices"][0]["message"]["content"].strip()
                raw = raw.strip("`").strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()
                topics = json.loads(raw)
                if isinstance(topics, list) and all(isinstance(t, str) for t in topics):
                    return topics[:4]
            except Exception as e:
                print(f"Ошибка ({model}): {e}")
                continue
    return []