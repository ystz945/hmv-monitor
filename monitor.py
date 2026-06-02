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
            page.goto(URL, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(3000)
            
            # 必须在逻辑结束前写入文件，否则 Artifacts 找不到文件
            with open("downloaded_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
                
            text = page.locator("body").inner_text()
            
            # 判定逻辑
            is_sold_out = any(word in text for word in ["注文不可", "申し訳ございませんが現在ご注文いただけません", "現在オンラインでご注文いただけません"])
            has_cart = "カートに入れる" in text or "カートへ" in text
            
            # 补货提醒
            if not is_sold_out and has_cart:
                send_wx_notification(f"🔔【HMV补货提醒】商品已补货，请立即前往抢购！\n链接: {URL}")
                print("💥 补货通知已推送")
            # 6小时简报
            elif current_count % 36 == 0:
                send_wx_notification(f"🤖【监控运行简报】系统已连续运行 6 小时。\n当前运行次数: {current_count} 次。\n状态: 商品仍无货，监控中。")
                print("📊 6小时心跳通知已推送")
            else:
                print(f"🔒 运行第 {current_count} 次：仍无货，保持静默。")
        
        except Exception as e:
            print(f"监控出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_stock()
