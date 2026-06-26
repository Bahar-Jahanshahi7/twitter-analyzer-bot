import os
import asyncio
import json
import urllib.request
import html
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TXT_FILE = "sent_links.txt"

# کلمات کلیدی ارزشمند شما برای فیلتر کردن اخبار مهم
KEYWORDS = [
    "upgrade", "mainnet", "V2", "V3", "V4", "launch",
    "protocol change", "governance vote", "proposal passed",
    "tokenomics update", "emission change", "burn", "buyback", 
    "revenue", "fees generated", "TVL increase", "inflows", 
    "outflows", "institutional", "onchain activity", "volume growth"
]

# لیست نماد (Ticker) پروژه‌های شما برای مانیتور دقیق‌تر
PROJECT_TICKERS = [
    "ETH", "BNB", "USDC", "TON", "HBAR", "SUI", "NEAR", "WORLD", "ONDO", 
    "DFI", "RNDR", "ALGO", "JUP", "INJ", "NEXO", "AERO", "LDO", "PENDLE"
]

if os.path.exists(TXT_FILE):
    with open(TXT_FILE, "r") as f:
        SENT_LINKS = set(line.strip() for line in f if line.strip())
else:
    with open(TXT_FILE, "w") as f:
        f.write("")
    SENT_LINKS = set()

def save_link(link):
    with open(TXT_FILE, "a") as f:
        f.write(f"{link}\n")
    SENT_LINKS.add(link)

async def main_pipeline():
    print("Checking crypto insights via CryptoPanic Aggregator API...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # 🔑 یک API Key رایگان از سایت Cryptopanic.com بگیرید و جایگزین کنید (یا در Secrets گیت‌هاب بگذارید)
    # اگر تمایل دارید کاملاً بدون توکن باشد، می‌توان از فید RSS عمومی آن‌ها نیز استفاده کرد.
    API_KEY = "YOUR_CRYPTOPANIC_FREE_API_KEY" 
    
    # لینک فید اخبار کریپتو (نسخه عمومی بدون نیاز به کلید هم برای تست کار می‌کند)
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={API_KEY}&public=true&kind=news"
    if API_KEY == "YOUR_CRYPTOPANIC_FREE_API_KEY":
        url = "https://cryptopanic.com/api/v1/posts/?public=true&kind=news"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    async with bot:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            posts = data.get("results", [])
            
            for post in posts:
                post_link = post.get("url") or post.get("id")
                if not post_link or str(post_link) in SENT_LINKS:
                    continue
                
                title = post.get("title", "")
                currencies = [c.get("code", "").upper() for c in post.get("currencies", [])]
                
                # ۱. بررسی اینکه آیا خبر مربوط به یکی از پروژه‌های درخواستی شما هست یا خیر
                is_relevant_project = any(ticker in currencies for ticker in PROJECT_TICKERS) or len(PROJECT_TICKERS) == 0
                
                if is_relevant_project:
                    # ۲. بررسی کلمات کلیدی در عنوان خبر
                    contains_keyword = any(keyword.lower() in title.lower() for keyword in KEYWORDS)
                    
                    if contains_keyword:
                        safe_title = html.escape(title)
                        project_tags = ", ".join([f"#{c}" for c in currencies])
                        
                        final_message = (
                            f"🔔 <b>خبر جدید دامنه‌های بنیادی ({project_tags})</b>\n\n"
                            f"📝 <b>عنوان:</b>\n{safe_title}\n\n"
                            f"🔗 <a href='{post.get('url')}'>لینک منبع خبر</a>"
                        )
                        
                        try:
                            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message, parse_mode="HTML")
                            print(f"✅ Message sent: {title[:30]}")
                            save_link(str(post_link))
                        except Exception as tg_err:
                            print(f"❌ Telegram Error: {tg_err}")
                            
        except Exception as e:
            print(f"⚠️ Error fetching from CryptoPanic: {e}")

if __name__ == "__main__":
    asyncio.run(main_pipeline())
