"""网页抓取工具 — 纯文本抓取 + JS渲染抓取"""
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def fetch_website_content(url: str):
    """抓取网页纯文本内容（不支持JS渲染的页面）"""
    try:
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/125.0.0.0 Safari/537.36"),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=20,
                            verify=False, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        return soup.get_text(separator='\n', strip=True)[:8000], None
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP 错误：{e.response.status_code} {e.response.reason}"
    except requests.exceptions.Timeout:
        return None, "网页抓取超时，请检查域名是否正确"
    except requests.exceptions.ConnectionError:
        return None, "无法连接到网站，请检查域名是否正确"
    except Exception as e:
        return None, f"网页抓取失败：{e}"


def fetch_website_content_js(url: str, wait_time: int = 3000):
    """抓取JS渲染后的网页内容（需要Playwright）"""
    try:
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/125.0.0.0 Safari/537.36")
            )
            page.goto(url, timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(wait_time)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)[:8000]

        if not text.strip():
            return None, "页面渲染后仍未提取到文字内容，可能需要更长等待时间或网站有反爬限制"

        return text, None

    except Exception as e:
        return None, f"JS渲染抓取失败：{e}"
