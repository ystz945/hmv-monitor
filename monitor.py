import os
import requests
from playwright.sync_api import sync_playwright

# ==================== 配置区 ====================
URL = "https://www.hmv.co.jp/artist_South-Club_000000000718535/item_2nd-EP-20_8866649"
COUNTER_FILE = ".monitor_counter.txt"
# ================================================

WX_APP_TOKEN = os.getenv("WX_APP_TOKEN")
WX_UID = os.getenv("WX_UID")

def get_and_update_count():
    count = 0
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r') as f:
                count = int(f.read().strip())
        except:
            count = 0
    count += 1
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(count))
    return count

def send_wx_notification(text):
    wx_url = "https://wxpusher.zjiecode.com/api/send/message"
    payload = {"appToken": WX_APP_TOKEN, "content": text, "contentType": 1, "uids": [WX_UID]}
    try:
        requests.post(wx_url, json=payload, timeout=8)
    except:
        pass

def check_stock():
    current_count = get_and_update_count()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", locale="ja-JP")
        page = context.new_page()
        
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            with open("downloaded_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
                
            text = page.locator("body").inner_text()
            
            is_sold_out = any(word in text for word in ["注文不可", "申し訳ございませんが現在ご注文いただけません", "現在オンラインでご注文いただけません"])
            has_cart = "カートに入れる" in text or "カートへ" in text
            
            if not is_sold_out and has_cart:
                send_wx_notification(f"🔔【HMV补货提醒】商品已补货！\n链接: {URL}")
                print("💥 补货通知已推送")
            elif current_count % 36 == 0:
                send_wx_notification(f"🤖【监控报平安】\n系统已安全挂机 6 小时。\n运行次数: {current_count} 次。\n状态: 无货中。")
                print("📊 6小时心跳通知已推送")
            else:
                print(f"🔒 运行第 {current_count} 次：仍无货，保持静默。")
        
        except Exception as e:
            print(f"监控出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_stock()
