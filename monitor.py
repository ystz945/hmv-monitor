import os
import requests
from bs4 import BeautifulSoup

# ==================== 配置区 ====================
URLS = [
    "https://www.hmv.co.jp/artist_%E3%82%A2%E3%83%8B%E3%83%A1_000000000013179/item_%E6%9C%AA%E6%9D%A5%E6%97%A5%E8%A8%98-Blu-ray-%E9%99%90%E5%AE%9A%E7%89%88-%E7%AC%AC9%E5%B7%BB_4215832"
]
COUNTER_FILE = ".monitor_counter.txt"
# ================================================

WX_APP_TOKEN = os.getenv("WX_APP_TOKEN")
WX_UID = os.getenv("WX_UID")

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.hmv.co.jp/"
}

def get_and_update_count():
    """读取并更新运行次数（持久化在本地文件中）"""
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
            print(f"正在检查商品: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"网页请求失败，状态码: {response.status_code}，本次跳过。")
                continue
            
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            try:
                test_soup = BeautifulSoup(response.content, 'html.parser')
                if test_soup.title and "" in test_soup.title.text:
                    response.encoding = 'shift_jis'
            except:
                pass

            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.text
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"抓取到的网页标题为: {title}")
            
            # 严格正向匹配
            is_buyable_button_present = "カートに入れる" in page_text
            
            if is_buyable_button_present:
                if "HMV" not in title and "未来日記" not in title:
                    print("警告：虽匹配到关键字，但网页标题异常，跳过发送。")
                    continue
                    
                msg = f"🔔【HMV补货提醒】\n您监控的特价商品已确切放出了「加入购物车」按钮！请速度前往抢购！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 确认补货，通知已发出！")
            else:
                print(f"检查结果：未检测到购物车按钮。当前累计后台运行次数: {current_count} 次。")
                
                # 每 6 小时（每10分钟一次，6小时正好是第 36 次、72 次...）发送一次运行简报
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
        # 获取最新的运行次数
        current_count = get_and_update_count()
        check_stock(current_count)
