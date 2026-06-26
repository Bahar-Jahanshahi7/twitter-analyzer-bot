import os
import asyncio
import xml.etree.ElementTree as ET
import urllib.request
import html
import re
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TXT_FILE = "sent_links.txt"

# 🧪 لیست موقت فقط برای تستِ ارسال ربات:
KEYWORDS = ["crypto", "bitcoin", "market", "the", "price", "new"]
PROJECTS = ["crypto", "bitcoin", "market", "the", "price", "new"]

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
    print("Checking crypto insights via Free Public RSS Feed...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # استفاده از فید RSS عمومی و رایگان CryptoPanic (این لینک نیازی به API Key ندارد)
    rss_url = "https://cryptopanic.com/news/rss/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    async with bot:
        try:
            req = urllib.request.Request(rss_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:25] # بررسی ۲۵ خبر آخر بازار
            
            for item in items:
                link = item.find('link').text if item.find('link') is not None else ""
                
                if not link or link in SENT_LINKS:
                    continue
                
                title = item.find('title').text if item.find('title') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                
                full_text = f"{title} {description}"
                
                # ۱. بررسی اینکه آیا خبر مربوط به پروژه‌های شما هست؟
                is_relevant_project = any(project.lower() in full_text.lower() for project in PROJECTS)
                
                if is_relevant_project:
                    # ۲. بررسی وجود کلمات کلیدی بنیادی شما
                    contains_keyword = any(keyword.lower() in full_text.lower() for keyword in KEYWORDS)
                    
                    if contains_keyword:
                        safe_title = html.escape(title)
                        
                        # پیدا کردن اینکه خبر دقیقاً مربوط به کدام پروژه شماست برای تگ کردن
                        found_projects = [p for p in PROJECTS if p.lower() in full_text.lower()]
                        tags = ", ".join([f"#{p}" for p in found_projects[:3]])
                        
                        final_message = (
                            f"🔔 <b>تحول بنیادی جدید ({tags})</b>\n\n"
                            f"📝 <b>عنوان خبر:</b>\n{safe_title}\n\n"
                            f"🔗 <a href='{link}'>مشاهده کامل منبع خبر</a>"
                        )
                        
                        try:
                            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message, parse_mode="HTML")
                            print(f"✅ Alert sent: {title[:30]}...")
                            save_link(link)
                        except Exception as tg_err:
                            print(f"❌ Telegram Error: {tg_err}")
                            
        except Exception as e:
            print(f"⚠️ Error fetching public RSS: {e}")

if __name__ == "__main__":
    asyncio.run(main_pipeline())
