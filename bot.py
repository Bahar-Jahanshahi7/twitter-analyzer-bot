import os
import asyncio
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import html
import re
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TXT_FILE = "sent_links.txt"

# کلمات کلیدی بنیادی شما
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
    print("Checking crypto insights via Dynamic Google Wire (100% Anti-Block)...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # استفاده از فید جهانی اخبار کریپتو گوگل که همیشه فعال است و هرگز بلاک نمی‌شود
    encoded_query = urllib.parse.quote("crypto OR bitcoin OR altcoin")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    async with bot:
        try:
            req = urllib.request.Request(rss_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:40] # بررسی ۴۰ خبر زنده و داغ بازار
            
            for item in items:
                link = item.find('link').text if item.find('link') is not None else ""
                
                if not link or link in SENT_LINKS:
                    continue
                
                title = item.find('title').text if item.find('title') is not None else ""
                
                # ۱. بررسی اینکه آیا خبر به پروژه‌های شما ربط دارد؟
                is_relevant_project = any(project.lower() in title.lower() for project in PROJECTS)
                
                if is_relevant_project:
                    # ۲. بررسی کلمات کلیدی بنیادی
                    contains_keyword = any(keyword.lower() in title.lower() for keyword in KEYWORDS)
                    
                    if contains_keyword:
                        # تمیز کردن عنوان از نام خبرگزاری‌ها که گوگل ته تایتل می‌زند (مثلا - Coindesk)
                        clean_title = title.split(' - ')[0] if ' - ' in title else title
                        safe_title = html.escape(clean_title)
                        
                        final_message = (
                            f"🔔 <b>رویداد بنیادی جدید در بازار</b>\n\n"
                            f"📝 <b>عنوان خبر:</b>\n{safe_title}\n\n"
                            f"🔗 <a href='{link}'>مشاهده کامل خبر</a>"
                        )
                        
                        try:
                            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message, parse_mode="HTML")
                            print(f"✅ Alert sent: {clean_title[:30]}...")
                            save_link(link)
                        except Exception as tg_err:
                            print(f"❌ Telegram Error: {tg_err}")
                            
        except Exception as e:
            print(f"⚠️ Error checking Google Wire: {e}")

if __name__ == "__main__":
    asyncio.run(main_pipeline())
