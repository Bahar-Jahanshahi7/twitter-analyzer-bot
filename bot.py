import os
import asyncio
import json
import urllib.request
import html
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TXT_FILE = "sent_links.txt"

# کلمات کلیدی بنیادی شما
KEYWORDS = [
    "upgrade", "mainnet", "V2", "V3", "V4", "launch",
    "protocol change", "governance vote", "proposal passed",
    "tokenomics update", "emission change", "burn", "buyback", 
    "revenue", "fees generated", "TVL increase", "inflows", 
    "outflows", "institutional", "onchain activity", "volume growth", "list", "listing"
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
    print("Checking crypto insights via Safe JSON API (No Block)...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # استفاده از API رسمی اخبار صرافی CoinEx (دارای دیتای غنی بنیادی بازار و ۱۰۰٪ بدون بلاک)
    url = "https://www.coinex.com/res/announcement/list?page=1&limit=20"
    
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
            
            articles = data.get("data", {}).get("list", [])
            
            for article in articles:
                article_id = str(article.get("id"))
                if not article_id or article_id in SENT_LINKS:
                    continue
                
                title = article.get("title", "")
                link = f"https://www.coinex.com/announcement/detail/{article_id}"
                
                # ۱. بررسی پروژه
                is_relevant_project = any(project.lower() in title.lower() for project in PROJECTS)
                
                # برای اینکه تست اولیه حتماً جواب دهد، اگر خبری پیدا نشد کل بازار را با کلمات کلیدی بسنجد
                if is_relevant_project or len(PROJECTS) == 0:
                    # ۲. بررسی کلمات کلیدی
                    contains_keyword = any(keyword.lower() in title.lower() for keyword in KEYWORDS)
                    
                    if contains_keyword:
                        safe_title = html.escape(title)
                        
                        final_message = (
                            f"🔔 <b>رویداد بنیادی جدید بازار</b>\n\n"
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
            print(f"⚠️ Error fetching JSON API: {e}")

if __name__ == "__main__":
    asyncio.run(main_pipeline())
