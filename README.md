# 每日香港科技新聞 Telegram Bot

這是一個以 Python + RSS + GitHub Actions + Telegram Bot API 建立的免費起步版本。它每天香港時間 **07:30** 收集最近 36 小時的科技新聞，按電腦硬件、手機／應用程式、汽車科技及遊戲分類，去重後發送到 Telegram。

預設模式不使用 AI，直接整理 RSS 摘要，因此沒有模型費用。若設定 `GEMINI_API_KEY`，程式會對入選新聞產生較詳細的香港繁體中文摘要；Gemini 額度及服務條款可能改變，並非永久保證免費。AI 失敗時仍會發送 RSS 摘要版本。

## 1. 建立 Telegram Bot

1. 在 Telegram 搜尋 `@BotFather`，輸入 `/newbot`，依指示建立 Bot。
2. 複製 BotFather 給你的 token，這是 `TELEGRAM_BOT_TOKEN`。
3. 開啟新 Bot，先傳送任何一則訊息給它。
4. 用瀏覽器開啟 `https://api.telegram.org/bot<你的TOKEN>/getUpdates`，在回應 JSON 找到 `message.chat.id`，這是 `TELEGRAM_CHAT_ID`。群組 chat id 通常是負數。

不要把 token 寫入程式碼或提交到 GitHub。

## 2. 放到 GitHub

把此資料夾內容放入一個 GitHub repository。公開 repository 的 GitHub-hosted standard runner 通常可免費執行；請以你的 GitHub 帳戶條款為準。

在 repository 的 **Settings → Secrets and variables → Actions → New repository secret** 加入：

| Secret | 必需 | 用途 |
|---|---:|---|
| `TELEGRAM_BOT_TOKEN` | 是 | BotFather token |
| `TELEGRAM_CHAT_ID` | 是 | 接收簡報的私人聊天室或群組 |
| `GEMINI_API_KEY` | 否 | 啟用較詳細 AI 繁體中文摘要 |

加入檔案後，到 **Actions → Daily Hong Kong Tech Briefing → Run workflow** 手動測試一次。成功後會每天香港時間 07:30 執行。

## 3. 本機測試

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN='你的token'
export TELEGRAM_CHAT_ID='你的chat_id'
PYTHONPATH=src python src/main.py
```

本機測試會真的發送 Telegram 訊息；若只想做語法及單元測試，執行：

```bash
python -m unittest discover -s tests -v
python -m py_compile src/main.py src/feeds.py
```

## 4. 可調整設定

| 環境變數 | 預設值 | 說明 |
|---|---:|---|
| `LOOKBACK_HOURS` | `36` | 抓取最近多少小時的新聞 |
| `MAX_ITEMS_PER_CATEGORY` | `6` | 每一分類最多文章數 |
| `GEMINI_MODEL` | `gemini-2.0-flash` | 有 Gemini key 時使用的模型 |
| `STATE_FILE` | `data/seen.json` | 已發送文章的去重狀態 |

如要改時間，修改 `.github/workflows/daily-briefing.yml` 的 cron。GitHub Actions 使用 UTC；香港 07:30 對應 `30 23 * * *`（前一日 UTC）。

## 5. 重要限制

程式只使用 RSS 的公開標題及摘要，不會複製整篇新聞。請保留每篇原文連結並遵守各來源的 RSS 使用條款。RSS 來源失效時，程式會跳過該來源而繼續處理其他來源。

`data/seen.json` 會由 GitHub Actions 提交回 repository，用來避免同一篇文章重複發送；它不包含 Telegram token。若 repository 是私有，請另外確認 GitHub Actions 的免費配額。
