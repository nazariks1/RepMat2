import base64
import httpx
from config import OPENROUTER_API_KEY
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
VISION_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-4-maverick:free",
    "nvidia/nemotron-3-nano-omni-48b:free",
]
TASK_PROMPT = """Перед тобой фото или скриншот условия математической задачи.
Точно перепиши всё что написано:
- Весь текст условия
- Все числа, формулы, уравнения (например: x^2 + 3x - 4 = 0, дробь как a/b)
Не решай задачу. Только перепиши условие.
Отвечай на русском языке."""
SOLUTION_PROMPT = """Перед тобой фото рукописного решения математической задачи из тетради.
Точно перепиши всё что написано:
- Все шаги решения по порядку
- Все формулы и вычисления (степень как x^2, корень как sqrt(x), дробь как a/b)
- Итоговый ответ

Не исправляй ошибки — переписывай как есть. Неразборчивое место — пометь [неразборчиво].
Отвечай на русском языке. 
В ответе не используй никаких других слов, кроме непосредственного"""

def _to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

async def _call_vision(image_bytes: bytes, prompt: str) -> str:
    b64 = _to_base64(image_bytes)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://math-bot",
        "X-Title": "MathBot",
    }
    body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "max_tokens": 2500,
    }
    last_error = None
    async with httpx.AsyncClient(timeout=90) as client:
        for model in VISION_MODELS:
            try:
                body["model"] = model
                resp = await client.post(OPENROUTER_URL, headers=headers, json=body)
                if resp.status_code != 200:
                    print(f"Ошибка: {resp.text[:500]}")
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    continue
                data = resp.json()
                if "error" in data:
                    print(f"Ошибка: {data['error']}")
                    last_error = str(data["error"])
                    continue
                if not data.get("choices"):
                    print(f"Пустой choices: {data}")
                    last_error = "Пустой ответ от модели"
                    continue
                content = data["choices"][0]["message"]["content"]
                used_model = data.get("model", model)
                if content and len(content.strip()) > 5:
                    return content.strip()
                print("Ответ слишком короткий")
                last_error = "Пустой ответ"
            except Exception as e:
                print(f"Ошибка: {type(e).__name__}: {e}")
                last_error = str(e)
    raise RuntimeError(f"Все модели не ответили. Последняя ошибка: {last_error}")

async def recognize_task_image(image_bytes: bytes) -> str:
    try:
        return await _call_vision(image_bytes, TASK_PROMPT)
    except Exception as e:
        print(f"Ошибка: {e}")
        return (
            "[❌ Не удалось распознать изображение]\n\n"
            f"Причина: {e}\n\n"
        )

async def recognize_solution_images(images_list: list) -> str:
    if not images_list:
        return ""
    results = []
    failed_count = 0
    for i, img_bytes in enumerate(images_list, 1):
        try:
            text = await _call_vision(img_bytes, SOLUTION_PROMPT)
            results.append(f"--- Страница {i} ---\n{text}")
        except Exception as e:
            print(f"Ошибка фото {i}: {e}")
            failed_count += 1
            results.append(f"--- Страница {i} ---\n[Не распознано: {e}]")
    combined = "\n\n".join(results)
    if failed_count == len(images_list):
        return f"[❌ Не удалось распознать изображения]\n\n" + combined
    if failed_count > 0:
        combined += f"\n\n⚠️ Не распознано {failed_count} из {len(images_list)} фото"
    return combined