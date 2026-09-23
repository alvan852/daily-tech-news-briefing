"""Collect RSS news, create a Traditional Chinese briefing, and send it to Telegram."""
from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import feedparser
import requests

from feeds import CATEGORY_KEYWORDS, CATEGORY_NAMES, FEEDS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOG = logging.getLogger(__name__)
HK = ZoneInfo("Asia/Hong_Kong")
UTC = timezone.utc
MAX_ITEMS_PER_CATEGORY = int(os.getenv("MAX_ITEMS_PER_CATEGORY", "6"))
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "36"))
STATE_FILE = Path(os.getenv("STATE_FILE", "data/seen.json"))


def clean_text(value: Any) -> str:
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_") and k.lower() not in {"ref", "source", "fbclid", "gclid"}]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))


def parse_date(entry: Any) -> datetime:
    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if raw:
            try:
                date = parsedate_to_datetime(raw)
                return date.astimezone(UTC) if date.tzinfo else date.replace(tzinfo=UTC)
            except (TypeError, ValueError, IndexError):
                pass
    for key in ("published_parsed", "updated_parsed"):
        struct = entry.get(key)
        if struct:
            return datetime(*struct[:6], tzinfo=UTC)
    return datetime.now(UTC)


def classify(title: str, summary: str, hinted: str) -> tuple[str, int]:
    text = f"{title} {summary}".lower()
    scores = {category: sum(1 for word in words if word.lower() in text) for category, words in CATEGORY_KEYWORDS.items()}
    scores[hinted] += 2
    category = max(scores, key=scores.get)
    return category, scores[category]


def load_seen() -> set[str]:
    try:
        return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set()


def save_seen(seen: set[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Keep the state small enough for a public repository.
    STATE_FILE.write_text(json.dumps(sorted(seen)[-3000:], ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_news(seen: set[str]) -> list[dict[str, Any]]:
    cutoff = datetime.now(UTC) - timedelta(hours=LOOKBACK_HOURS)
    items: list[dict[str, Any]] = []
    for hinted, source, feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url, request_headers={"User-Agent": "daily-tech-news-briefing/1.0"})
            if getattr(feed, "bozo", False):
                LOG.warning("RSS warning from %s: %s", source, getattr(feed, "bozo_exception", "unknown"))
            for entry in feed.entries[:30]:
                url = normalize_url(entry.get("link", ""))
                title = clean_text(entry.get("title", ""))
                summary = clean_text(entry.get("summary", entry.get("description", "")))
                if not url or not title:
                    continue
                published = parse_date(entry)
                key = hashlib.sha256((url or title).encode()).hexdigest()
                if published < cutoff or key in seen:
                    continue
                category, score = classify(title, summary, hinted)
                items.append({"key": key, "category": category, "source": source, "title": title, "summary": summary[:1200], "url": url, "published": published.isoformat(), "score": score})
        except Exception as exc:  # One broken feed must not stop the daily message.
            LOG.warning("Could not read %s: %s", source, exc)
    # Deduplicate within this run and rank by keyword score then recency.
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        unique.setdefault(item["key"], item)
    return sorted(unique.values(), key=lambda x: (x["score"], x["published"]), reverse=True)


def generate_optional_ai_summary(items: list[dict[str, Any]]) -> dict[str, str]:
    """Use Gemini only when configured; otherwise return an empty map for zero-cost mode."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not items:
        return {}
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')}:generateContent?key={api_key}"
    result: dict[str, str] = {}
    for item in items:
        prompt = ("請用香港繁體中文寫一段 120 至 220 字新聞摘要。只可使用提供的資料，不可猜測；" "保留產品名稱、版本、日期及數字。格式：一句話結論：... 詳細摘要：... 影響：... 未確定：...\n" f"標題：{item['title']}\n來源摘要：{item['summary']}")
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500}}
        try:
            response = requests.post(endpoint, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text:
                result[item["key"]] = text
        except Exception as exc:
            LOG.warning("AI summary unavailable for %s: %s", item["title"], exc)
        time.sleep(0.2)
    return result


def build_briefing(items: list[dict[str, Any]], ai: dict[str, str]) -> str:
    now = datetime.now(HK).strftime("%Y-%m-%d %H:%M")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        if len(groups[item["category"]]) < MAX_ITEMS_PER_CATEGORY:
            groups[item["category"]].append(item)
    lines = [f"每日科技新聞簡報｜香港時間 {now}", "", f"今次收集 {len(items)} 篇候選新聞；內容為公開 RSS 摘要整理，請按連結閱讀原文。"]
    for category in ("hardware", "mobile", "auto", "gaming"):
        lines += ["", f"━━ {CATEGORY_NAMES[category]} ━━"]
        if not groups[category]:
            lines.append("今日暫未找到合資格新聞。")
            continue
        for index, item in enumerate(groups[category], 1):
            published = datetime.fromisoformat(item["published"]).astimezone(HK).strftime("%m-%d %H:%M")
            lines += [f"{index}. {item['title']}", f"來源：{item['source']}｜{published}"]
            detail = ai.get(item["key"])
            if not detail:
                detail = f"摘要：{item['summary'] or 'RSS 未提供摘要，請查看原文。'}"
            lines += [detail, f"原文：{item['url']}", ""]
    lines += ["", "提示：摘要只根據來源已提供內容；傳聞或未確認資料不應視為事實。"]
    return "\n".join(lines).strip()


def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    # Telegram text messages are limited to 4096 characters; split on paragraph boundaries.
    chunks: list[str] = []
    while len(text) > 3900:
        cut = text.rfind("\n\n", 0, 3900)
        cut = cut if cut > 500 else text.rfind("\n", 0, 3900)
        cut = cut if cut > 0 else 3900
        chunks.append(text[:cut].strip())
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    for chunk in chunks:
        response = requests.post(endpoint, json={"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True}, timeout=30)
        response.raise_for_status()
        if not response.json().get("ok"):
            raise RuntimeError(response.text)


def main() -> None:
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        raise RuntimeError("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    seen = load_seen()
    items = fetch_news(seen)
    selected = []
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        if counts[item["category"]] < MAX_ITEMS_PER_CATEGORY:
            selected.append(item)
            counts[item["category"]] += 1
    ai = generate_optional_ai_summary(selected)
    send_telegram(build_briefing(selected, ai))
    save_seen(seen.union(item["key"] for item in selected))
    LOG.info("Sent %d articles (%d AI summaries)", len(selected), len(ai))


if __name__ == "__main__":
    main()
