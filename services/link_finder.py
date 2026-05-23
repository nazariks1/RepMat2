
import asyncio
import httpx
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup

# ── Надёжные русскоязычные образовательные сайты ──────────────────────────────
TRUSTED_DOMAINS = [
    "ru.wikipedia.org",
    "mathus.ru",
    "mathprofi.ru",
    "mathprofi.net",
    "uchitel.pro",
    "foxford.ru",
    "math.ru",
    "nmat.ru",
    "statgrad.ru",
    "reshuege.ru",
    "allmath.ru",
    "matematika-na5.ru",
    "uznaem-math.ru",
    "fmclass.ru",
    "matematikaege.ru",
    "alexlarin.net",
    "yaklass.ru",
    "resh.edu.ru",
    "interneturok.ru",
    "mathedu.ru",
    "bymath.net",
    "cleverstudents.ru",
    "ru.khanacademy.org",
    "school-assistant.ru",
]

BLOCKED_DOMAINS = [
    "youtube.com", "youtu.be",
    "vk.com", "ok.ru",
    "instagram.com", "facebook.com",
    "amazon.com", "ebay.com",
    "avito.ru", "wildberries.ru",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

SEARCH_URL = "https://html.duckduckgo.com/html/"


async def _ddg_search(client: httpx.AsyncClient, query: str, max_results: int = 10) -> list[str]:
    """Делает поиск в DuckDuckGo и возвращает список URL."""
    try:
        resp = await client.post(
            SEARCH_URL,
            data={"q": query, "kl": "ru-ru"},
            headers=HEADERS,
        )
        if resp.status_code != 200:
            print(f"  ⚠️ DDG вернул {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []

        for a in soup.select("a.result__url"):
            href = a.get("href", "")
            if "uddg=" in href:
                qs = parse_qs(urlparse(href).query)
                real = qs.get("uddg", [""])[0]
                href = unquote(real)
            if href.startswith("http"):
                urls.append(href)
            if len(urls) >= max_results:
                break

        if not urls:
            for a in soup.select("a.result__a"):
                href = a.get("href", "")
                if href.startswith("http"):
                    urls.append(href)
                if len(urls) >= max_results:
                    break

        print(f"  🔍 DDG нашёл {len(urls)} URL для «{query}»")
        return urls

    except Exception as e:
        print(f"  ❌ DDG ошибка: {e}")
        return []


def _is_trusted(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower().lstrip("www.")
        for trusted in TRUSTED_DOMAINS:
            if domain == trusted or domain.endswith("." + trusted):
                return True
    except Exception:
        pass
    return False


def _is_blocked(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower().lstrip("www.")
        for blocked in BLOCKED_DOMAINS:
            if domain == blocked or domain.endswith("." + blocked):
                return True
    except Exception:
        pass
    return False


async def _check_alive(client: httpx.AsyncClient, url: str) -> bool:
    """Асинхронная проверка доступности ссылки."""
    try:
        r = await client.head(url, headers=HEADERS, follow_redirects=True)
        if r.status_code < 400:
            return True
        if r.status_code in (405, 403):
            r2 = await client.get(url, headers=HEADERS)
            return r2.status_code < 400
        return False
    except Exception:
        return False


async def find_links_for_topic(topic: str, max_links: int = 2) -> list[dict]:
    """
    Ищет max_links рабочих ссылок по одной теме.
    Возвращает список словарей: [{"title": str, "url": str}]
    """
    query = f"{topic} математика теория объяснение"

    async with httpx.AsyncClient(timeout=15) as client:
        all_urls = await _ddg_search(client, query, max_results=15)

        results = []
        checked = set()

        priority = [u for u in all_urls if _is_trusted(u) and not _is_blocked(u)]
        rest = [u for u in all_urls if u not in priority and not _is_blocked(u)]

        for url in priority + rest:
            if url in checked:
                continue
            checked.add(url)

            if await _check_alive(client, url):
                domain = urlparse(url).netloc.lstrip("www.")
                results.append({"title": domain, "url": url})
                print(f"  ✅ Живая ссылка: {url}")

            if len(results) >= max_links:
                break

            await asyncio.sleep(0.3)

    if not results:
        print(f"  ⚠️ Живых ссылок для «{topic}» не нашлось")

    return results


async def find_theory_links(topics: list[str], links_per_topic: int = 2) -> dict[str, list[dict]]:
    """
    Для каждой темы из списка ищет ссылки.
    Возвращает словарь: {тема: [{"title": ..., "url": ...}, ...]}
    """
    result = {}
    for topic in topics:
        print(f"\n📖 Ищу ссылки по теме: «{topic}»")
        links = await find_links_for_topic(topic, max_links=links_per_topic)
        if links:
            result[topic] = links
        await asyncio.sleep(0.5)

    return result
