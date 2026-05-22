import asyncio
import httpx
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup

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
    try:
        resp = await client.post(
            SEARCH_URL,
            data={"q": query, "kl": "ru-ru"},
            headers=HEADERS,
        )
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
        return urls

    except Exception as e:
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

async def _check_open(client: httpx.AsyncClient, url: str) -> bool:
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
    query = f"{topic} математика теория объяснение"
    async with httpx.AsyncClient(timeout=15) as client:
        all_urls = await _ddg_search(client, query, max_results=15)
        results = []
        checked = set()
        priority = [u for u in all_urls if _is_trusted(u)]
        rest = [u for u in all_urls if u not in priority]
        for url in priority + rest:
            if url in checked:
                continue
            checked.add(url)
            if await _check_open(client, url):
                domain = urlparse(url).netloc.lstrip("www.")
                results.append({"title": domain, "url": url})
            if len(results) >= max_links:
                break
            await asyncio.sleep(0.3)
    return results

async def find_theory_links(topics: list[str], links_per_topic: int = 2) -> dict[str, list[dict]]:
    result = {}
    for topic in topics:
        links = await find_links_for_topic(topic, max_links=links_per_topic)
        if links:
            result[topic] = links
        await asyncio.sleep(0.5)
    return result