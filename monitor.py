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

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.hmv.co.jp/"
}

def get_and_update_count():
    """读取并更新运行次数（通过本地文件结合 GitHub Cache 实现持久化）"""
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
            
            # 自动智能修正编码，防止日文解析为乱码
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.text
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"抓取到的网页标题为: {title
