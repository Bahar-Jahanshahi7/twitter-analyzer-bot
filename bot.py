import os
import time
import asyncio
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import html
from google import genai
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# لیست اکانت‌ها و کلمات کلیدی شما
TWITTER_ACCOUNTS = ['elonmusk', 'Binance', 'VitalikButerin']
KEYWORDS = ['crypto', 'bitcoin', 'btc', 'eth', 'launch', 'tesla', 'ai']

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def analyze_tweet_with_gemini(tweet_text):
    for attempt in range(3):
        try:
            prompt = f"""
            به عنوان یک تحلیل‌گر بازارهای مالی، متن توییت زیر را بررسی کن:
            "{tweet_text}"
            
            لطفاً خروجی را دقیقاً در این قالب فارسی بفرست (بدون استفاده از علامت ستاره یا کدهای فرمت‌دهی):
            معنی فارسی: [ترجمه روان متن]
            درجه اهمیت فاندامنتال: [یک عدد از 1 تا 10 بر اساس تاثیر روی بازار]
            توضیح کوتاه علت نمره: [یک خط توضیح]
            """
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "503" in str(e):
                print(f"Gemini is busy (Attempt {attempt + 1}/3). Waiting 15 seconds...")
                time.sleep(15)
            else:
                print(f"Error in Gemini: {e}")
                return None
    return None

async def main_pipeline():
    print("Checking tweets via Google News RSS Pipeline...")
    
    for account in TWITTER_ACCOUNTS:
        try:
            query = f'from:{account} site:twitter.com OR site:x.com'
            encoded_query = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:3]
            
            if not items:
                print(f"No recent indexed tweets found for @{account} on Google News right now.")
                continue

            for item in items:
                title = item.find('title').text if item.find('title') is not None else ""
                tweet_link = item.find('link').text if item.find('link') is not None else ""
                
                tweet_text = title.split(' - ')[0] if ' - ' in title else title
                
                contains_keyword = any(keyword.lower() in tweet_text.lower() for keyword in KEYWORDS)
                
                if contains_keyword:
                    analysis = analyze_tweet_with_gemini(tweet_text)
                    if analysis:
                        # استفاده از HTML برای فرار از ارور کاراکترهای خاص تلگرام
                        safe_tweet_text = html.escape(tweet_text)
                        safe_analysis = html.escape(analysis)
                        
                        final_message = (
                            f"🔔 <b>توییت جدید از: @{account}</b>\n\n"
                            f"🇬🇧 <b>متن انگلیسی:</b>\n{safe_tweet_text}\n\n"
                            f"🇮🇷 <b>تحلیل و ترجمه:</b>\n{safe_analysis}\n\n"
                            f"🔗 <a href='{tweet_link}'>لینک منبع</a>"
                        )
                        
                        try:
                            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message, parse_mode="HTML")
                            print(f"Message sent for @{account} successfully!")
                        except Exception as tg_err:
                            print(f"Error sending Telegram: {tg_err}")
                        
                        # رعایت سقف درخواست جمینای
                        print("Waiting 15 seconds before checking next tweet...")
                        time.sleep(15)
                        
        except Exception as e:
            print(f"Error checking @{account}: {e}")

if __name__ == "__main__":
    # اجرای کل پروسه در یک لوپ اصلی و پایدار
    asyncio.run(main_pipeline())
