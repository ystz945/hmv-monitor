import os
import requests
from playwright.sync_api import sync_playwright

# ==================== 配置区 ====================
URLS = [
    "https://www.hmv.co.jp/artist_South-Club_000000000718535/item_2nd-EP-20_8866649"
]
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
    payload = {
        "appToken": WX_APP_TOKEN,
        "content": text,
        "contentType": 1, 
        "uids": [WX_UID]
    }
    try:
        res = requests.post(wx_url, json=payload, timeout=8)
        print(f"微信推送结果: {res.json()}")
    except Exception as e:
        print(f"微信推送失败: {e}")

def check_stock_with_browser(current_count):
    with sync_playwright() as p:
        # 在后台隐形启动 Chromium 浏览器
        browser = p.chromium.launch(headless=True)
        
        # 完美模拟真实用户的浏览器上下文
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ja-JP",
            viewport={"width": 1280, "height": 800}
        )
        
        for url in URLS:
            try:
                page = context.new_page()
                print(f"🤖 模拟用户操作，正在用浏览器打开网页: {url}")
                
                # 打开网页并等待网络请求完全静默（即基础页面加载完毕）
                page.goto(url, wait_until="networkidle", timeout=45000)
                
                # 额外多等 3 秒，确保商品右侧的库存动态转圈圈（Loading）完全变成真实文字
                page.wait_for_timeout(3000)
                
                # 获取此时此刻，浏览器屏幕上渲染出来的所有可见文本
                page_text = page.locator("body").inner_text()
                title = page.title()
                
                print("--- 真实浏览器模拟判定面板 ---")
                print(f"  - 网页标题: {title}")
                print(f"  - 页面可视文字总长度: {len(page_text)}")
                
                # 🚨 【无货核心判定】：检索页面是否出现了你提供的精确无货词
                is_sold_out = (
                    "注文不可" in page_text or 
                    "申し訳ございませんが現在ご注文いただけません" in page_text or 
                    "現在オンラインでご注文いただけません" in page_text
                )
                
                # 🛒 【有货核心特征】：检索页面是否渲染出了加入购物车按钮文字
                has_cart_text = "カートに入れる" in page_text or "カートへ" in page_text
                
                print(f"  - 匹配到『断货/无法购买』文案: {is_sold_out}")
                print(f"  - 匹配到『加入购物车』按钮文案: {has_cart_text}")
                print("------------------------------")
                
                # 【终极补货判定公式】：
                # 只有当这几句断货词在页面上“完全消失”，且“出现了加入购物车”的文字，才确切判定为补货有货！
                if not is_sold_out and has_cart_text:
                    if "HMV" not in title:
                        print("警告：页面标题异常（可能触发了人机拦截），本次跳过发信。")
                        continue
                        
                    msg = f"🔔【HMV补货提醒】\n浏览器模拟成功！断货文案已消失，且页面已渲染出购物车按钮！\n\n商品：{title}\n链接：{url}"
                    send_wx_notification(msg)
                    print("💥 成功捕捉到有货状态！补货微信通知已发出！")
                else:
                    print(f"检查结果：商品当前仍处于『无货（注文不可）』状态。当前累计运行: {current_count} 次。")
                    
                    # 每 6 小时（36次）发送一次挂机简报
                    if current_count % 36 == 0:
                        report_msg = f"🤖【HMV监控运行简报】\n真浏览器模拟盯着系统已安全挂机 6 小时。\n当前累计运行次数：{current_count} 次。\n状态：商品依旧处于无货提示状态，继续为您静默站岗中。"
                        send_wx_notification(report_msg)
                        
            except Exception as page_err:
                print(f"模拟浏览器操作商品页时出错: {page_err}")
            finally:
                page.close()
                
        context.close()
        browser.close()

if __name__ == "__main__":
    if not WX_APP_TOKEN or not WX_UID:
        print("错误：未检测到微信通知的环境变量（Secrets）配置！")
    else:
        current_count = get_and_update_count()
        check_stock_with_browser(current_count)
