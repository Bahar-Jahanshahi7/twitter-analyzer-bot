import os
import asyncio
import json
import urllib.request
import html
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TXT_FILE = "sent_links.txt"

# کلمات کلیدی بنیادی و لیستینگ شما
KEYWORDS = [
    "upgrade", "mainnet", "V2", "V3", "V4", "launch",
    "protocol", "governance", "proposal", "tokenomics", 
    "burn", "buyback", "tvl", "listing", "list", "added", "support"
]

# پروژه‌های مدنظر شما
PROJECTS = [
    "Ethereum", "ETH", "BNB", "Circle", "USDC", "TON", "Hedera", "HBAR", 
    "Sui", "NEAR", "Worldnetwork", "Ondo", "Dexe", "Dfinity", "ICP", "Morpho", 
    "Render", "RNDR", "Algorand", "ALGO", "Jupiter", "JUP", "Injective", "INJ", 
    "Nexo", "Aerodrome", "Lido", "LDO", "Pendle", "LayerZero"
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
    print("Checking crypto insights via Stable Gate JSON API...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # API رسمی، پایدار و کاملاً رایگان اطلاعیه‌های صرافی Gate.io (تضمین عدم بلاک و عدم ارور 404)
    url = "https://api.gateio.ws/api/v4/delivery/announcements"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    async with bot:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                raw_data = response.read().decode('utf-8')
                data = json.loads(raw_data)
            
            # خروجی این API به صورت یک لیست مستقیم از مقالات است
            for article in data[:30]: # بررسی ۳۰ اطلاعیه اخیر بازار
                article_id = str(article.get("id"))
                if not article_id or article_id in SENT_LINKS:
                    continue
                
                title = article.get("title", "")
                link = article.get("url") or f"https://www.gate.io/announcements/article/{article_id}"
                
                # ۱. بررسی اینکه آیا خبر مربوط به پروژه‌های شماست؟
                is_relevant_project = any(project.lower() in title.lower() for project in PROJECTS)
                
                if is_relevant_project:
                    # ۲. بررسی کلمات کلیدی بنیادی شما
                    contains_keyword = any(keyword.lower() in title.lower() for keyword in KEYWORDS)
                    
                    if contains_keyword:
                        safe_title = html.escape(title)
                        
                        final_message = (
                            f"📢 <b>رویداد بنیادی جدید در بازار (Gate)</b>\n\n"
                            f"📝 <b>عنوان:</b>\n{safe_title}\n\n"
                            f"🔗 <a href='{link}'>مشاهده کامل منبع</a>"
                        )
                        
                        try:
                            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message, parse_mode="HTML")
                            print(f"✅ Alert sent: {title[:30]}...")
                            save_link(article_id)
                        except Exception as tg_err:
                            print(f"❌ Telegram Error: {tg_err}")
                            
        except Exception as e:
            print(f"⚠️ Error fetching Gate JSON API: {e}")

if __name__ == "__main__":
    asyncio.run(main_pipeline())
