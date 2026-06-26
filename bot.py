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
    "protocol", "governance", "proposal", "tokenomics", 
    "burn", "buyback", "tvl", "listing", "list", "added", "support"
]

# پروژه‌های مدنظر شما (به صورت نام کامل یا نماد)
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
    print("Checking crypto insights via Rock-Solid CoinGecko API...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # 🔑 پایدارترین API رایگان کریپتو در دنیا برای آپدیت‌های وضعیت پروژه‌ها
    url = "https://api.coingecko.com/api/v3/status_updates?per_page=50"
    
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
            
            updates = data.get("status_updates", [])
            
            for update in updates:
                # شناسه یکتای هر خبر برای جلوگیری از ارسال تکراری
                project_name = update.get("project", {}).get("name", "")
                description = update.get("description", "")
                
                # ترکیب نام پروژه و متن برای ساخت یک شناسه یکتا جهت ذخیره در فایل متنی
                unique_id = str(hash(description[:50] + project_name))
                
                if unique_id in SENT_LINKS:
                    continue
                
                full_text = f"{project_name} {description}"
                
                # ۱. بررسی اینکه آیا مربوط به پروژه‌های شماست؟
                is_relevant_project = any(project.lower() in full_text.lower() for project in PROJECTS)
                
                if is_relevant_project:
                    # ۲. بررسی کلمات کلیدی بنیادی
                    contains_keyword = any(keyword.lower() in full_text.lower() for keyword in KEYWORDS)
                    
                    if contains_keyword:
                        # پاک‌سازی متن از تگ‌های HTML احتمالی کوین‌گکو
                        clean_desc = re.sub('<[^<]+?>', '', description)
                        safe_desc = html.escape(clean_desc[:500]) # محدود کردن طول پیام
                        
                        final_message = (
                            f"🔔 <b>رویداد بنیادی جدید ({project_name})</b>\n\n"
                            f"📝 <b>توضیحات:</b>\n{safe_desc}...\n\n"
                            f"ℹ️ <i>منبع: CoinGecko Status Updates</i>"
                        )
                        
                        try:
                            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message, parse_mode="HTML")
                            print(f"✅ Alert sent for {project_name}!")
                            save_link(unique_id)
                        except Exception as tg_err:
                            print(f"❌ Telegram Error: {tg_err}")
                            
        except Exception as e:
            print(f"⚠️ Error fetching CoinGecko API: {e}")

if __name__ == "__main__":
    asyncio.run(main_pipeline())
