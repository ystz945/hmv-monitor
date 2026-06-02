import os
import requests
from bs4 import BeautifulSoup

# ==================== 配置区 ====================
# 目前放的是你用来测试的有货商品链接
URLS = [
    "https://www.hmv.co.jp/artist_South-Club_000000000718535/item_2nd-EP-20_8866649"
]
COUNTER_FILE = ".monitor_counter.txt"
# ================================================

WX_APP_TOKEN = os.getenv("WX_APP_TOKEN")
WX_UID = os.getenv("WX_UID")

# 【核心改进】：改用标准的手机端浏览器 User-Agent，迫使 HMV 返回直接包含文本的轻量版页面
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.hmv.co.jp/"
}

def get_and_update_count():
    """读取并更新运行次数"""
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
    """通过 WxPusher 推送消息到微信"""
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

def check_stock(current_count):
    for url in URLS:
        try:
            print(f"正在检查商品(移动端模式): {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"网页请求失败，状态码: {response.status_code}，本次跳过。")
                continue
            
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.text
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"抓取到的网页标题为: {title}")
            
            # ===== 【🚨 修复后的 DEBUG 诊断区】 =====
            print("--- 移动端 DEBUG 诊断信息开始 ---")
            print(f"手机版网页总字数: {len(page_text)}")
            print("手机版网页前 400 个字内容:")
            print(page_text[:400].replace('\n', ' '))
            
            # 修复了此处 f-string 的单双引号嵌套错误
            has_js_warn = "JavaScriptを有効" in page_text
            print(f"  - 手机版是否依然提示需要JS: {has_js_warn}")
            print(f"  - 是否包含 'カート': {'カート' in page_text}")
            print(f"  - 是否包含 '入れる': {'入れる' in page_text}")
            print("--- 移动端 DEBUG 诊断信息结束 ---")
            # ===============================
            
            # 判定一：全网页纯文本检索是否存在“加入购物车”
            is_buyable_text = "カートに入れる" in page_text
            
            # 判定二：直接在源码中寻找是否有加入购物车的表单按钮（双重保险）
            is_btn_present = soup.find(id="js-addCart") is not None or "addcart" in response.text.lower()
            
            # 只要满足纯文本存在，或者找到了购物车交互特征，且没有被JS提示拦截
            if (is_buyable_text or is_btn_present) and not has_js_warn:
                if "HMV" not in title and "未来日記" not in title:
                    print("警告：虽匹配到关键字，但网页标题异常，跳过发送。")
                    continue
                    
                msg = f"🔔【HMV补货提醒】\n您监控的商品已确切放出了「加入购物车」按钮！请速度前往抢购！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 确认补货，通知已发出！")
            else:
                print(f"检查结果：未检测到购物车按钮。当前累计后台运行次数: {current_count} 次。")
                
                # 每 6 小时发送一次运行简报
                if current_count % 36 == 0:
                    report_msg = f"🤖【HMV监控运行简报】\n系统已持续为您盯梢 6 小时。\n当前累计安全运行次数：{current_count} 次。\n商品状态：依旧处于『注文不可』，未检测到补货。系统继续监控中！"
                    print("📊 达到 6 小时周期，正在发送运行次数日志...")
                    send_wx_notification(report_msg)
                
        except Exception as e:
            print(f"请求商品页面出错: {e}")

if __name__ == "__main__":
    if not WX_APP_TOKEN or not WX_UID:
        print("错误：未检测到微信通知的环境变量配置！")
    else:
        current_count = get_and_update_count()
        check_stock(current_count)
