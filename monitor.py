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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36", 
            locale="ja-JP",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 使用 domcontentloaded 规避网络超时，通过滚动触发懒加载
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(2000)
            
            # 【保留】原生 HTML 源码快照 —— 留给 AI/Gemini 深度分析 DOM 结构
            with open("downloaded_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            
            # 【新增】全页滚动截图 —— 留给用户直观排查是否遭遇 403 封锁或验证码
            page.screenshot(path="downloaded_page.png", full_page=True)
            
            text = page.locator("body").inner_text()
            
            # 判定逻辑
            is_sold_out = any(word in text for word in ["注文不可", "申し訳ございませんが现在ご注文いただけません", "申し訳ございませんが現在ご注文いただけません"])
            has_cart = "カートに入れる" in text or "カートへ" in text
            is_backorder = "お取り寄せ" in text
            
            if not is_sold_out and has_cart and not is_backorder:
                send_wx_notification(f"🔔【HMV现货补货】商品已上架！\n链接: {URL}")
                print("💥 现货推送已触发")
            elif current_count % 36 == 0:
                send_wx_notification(f"🤖【监控心跳】运行第 {current_count} 次，状态：无现货。")
                print("📊 6小时心跳通知")
            else:
                print(f"🔒 运行第 {current_count} 次：无货或调货中，保持静默。")
        
        except Exception as e:
            print(f"监控异常: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_stock()
