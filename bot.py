import os
import asyncio
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import html
import sqlite3
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# نام فایل دیتابیس برای ذخیره لینک‌های ارسال شده
DB_FILE = "sent_tweets.db"

TWITTER_ACCOUNTS = [
    "ethereum", "BNBCHAIN", "circle", "CantonNetwork", "ton_blockchain",
    "hedera", "SuiNetwork", "NEARProtocol", "worldnetwork", "OndoFoundation",
    "Aster_DEX", "DexeNetwork", "dfinity", "Morpho", "rendernetwork",
    "AlgoFoundation", "Stable", "JupiterExchange", "injective", "Nexo",
    "pudgypenguins", "Lighter_xyz", "AerodromeFi", "LidoFinance", "pendle_fi",
    "SonicLabs", "soon_svm", "AttentionToken", "MatrixAINetwork", "kamino",
    "0xfluid", "ether-fi", "LayerZero_Fndn"
]

KEYWORDS = [
    "upgrade", "mainnet", "V2", "V3", "V4", "launch",
    "protocol change", "governance vote", "proposal passed",
    "tokenomics update", "emission change", "burn", "buyback", 
    "revenue", "fees generated", "TVL increase", "inflows", 
    "outflows", "institutional", "onchain activity", "volume growth"
]

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def init_db():
    """ایجاد دیتابیس و جدول ذخیره لینک‌ها در صورت عدم وجود"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_links (
            link TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_already_sent(link):
    """بررسی اینکه آیا این لینک قبلاً ارسال شده است یا خیر"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_links WHERE link = ?", (link,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_link(link):
    """ذخیره لینک جدید در دیتابیس پس از ارسال موفق"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sent_links (link) VALUES (?)", (link,))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        pass  # لینک از قبل وجود داشته است

async def main_pipeline():
    print("Checking tweets via Google News RSS Pipeline...")
    
    # اطمینان از آماده بودن دیتابیس
    init_db()
    
    for account in TWITTER_ACCOUNTS:
        try:
            query = f'site:x.com/{account} OR site:twitter.com/{account}'
            encoded_query = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:3]
            
            if not items:
                print(f"No recent indexed tweets found for @{account} on Google News.")
                await asyncio.sleep(1)
                continue

            for item in items:
                title = item.find('title').text if item.find('title') is not None else ""
                tweet_link = item.find('link').text if item.find('link') is not None else ""
                
                # ۱. بررسی تکراری نبودن لینک پیش از هر کاری
                if not tweet_link or is_already_sent(tweet_link):
                    continue
                
                tweet_text = title.split(' - ')[0] if ' - ' in title else title
                contains_keyword = any(keyword.lower() in tweet_text.lower() for keyword in KEYWORDS)
                
                if contains_keyword:
                    safe_tweet_text = html.escape(tweet_text)
                    
                    final_message = (
                        f"🔔 <b>توییت جدید از: @{account}</b>\n\n"
                        f"📝 <b>متن توییت:</b>\n{safe_tweet_text}\n\n"
                        f"🔗 <a href='{tweet_link}'>لینک منبع (گوگل نیوز)</a>"
                    )
                    
                    try:
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message, parse_mode="HTML")
                        print(f"Message sent for @{account} successfully!")
                        
                        # ۲. ذخیره در دیتابیس پس از ارسال موفقیت‌آمیز
                        save_link(tweet_link)
                        
                    except Exception as tg_err:
                        print(f"Error sending Telegram: {tg_err}")
            
            await asyncio.sleep(2)
                        
        except Exception as e:
            print(f"Error checking @{account}: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main_pipeline())
