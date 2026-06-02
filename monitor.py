import os
import requests
from bs4 import BeautifulSoup

# ==================== 配置区 ====================
# 填入你需要监控的 HMV 商品链接列表
URLS = [
    "https://www.hmv.co.jp/artist_%E3%82%A2%E3%83%8B%E3%83%A1_000000000013179/item_%E6%9C%AA%E6%9D%A5%E6%97%A5%E8%A8%98-Blu-ray-%E9%99%90%E5%AE%9A%E7%89%88-%E7%AC%AC9%E5%B7%BB_4215832"
]
# ================================================

WX_APP_TOKEN = os.getenv("WX_APP_TOKEN")
WX_UID = os.getenv("WX_UID")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}

def send_wx_notification(text):
    """通过 WxPusher 推送消息到微信"""
    wx_url = "https://wxpusher.zhaojin97.cn/api/send/message"
    payload = {
        "appToken": WX_APP_TOKEN,
        "content": text,
        "contentType": 1, 
        "uids": [WX_UID]
    }
    try:
        res = requests.post(wx_url, json=payload, timeout=5)
        print(f"微信推送结果: {res.json()}")
    except Exception as e:
        print(f"微信推送失败: {e}")

def check_stock():
    for url in URLS:
        try:
            print(f"正在检查商品: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"网页请求失败，状态码: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. 寻找右侧购买状态区域
            # HMV 右侧下单面板通常包裹在 class 为 "p-order-box" 或 "order-box" 的 div 中，或者直接抓取关键文本
            page_text = soup.text
            
            # 2. 精准研判右侧状态
            is_order_unavailable = "注文不可" in page_text
            is_button_disabled = "現在オンラインでご注文いただけません" in page_text
            
            # 如果这两个代表“断货”的特征有任意一个消失了，说明按钮或状态变了！
            if not is_order_unavailable or not is_button_disabled:
                msg = f"🔔【HMV补货提醒】\n右侧的『注文不可』或『灰色按钮』状态已发生变动！可能补货或开放购买了，快冲！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 状态发生变动，通知已发出！")
            else:
                print("检查结果：依旧处于『注文不可』且按钮为灰色。")
                
        except Exception as e:
            print(f"请求商品页面出错: {e}")

if __name__ == "__main__":
    if not WX_APP_TOKEN or not WX_UID:
        print("错误：未检测到微信通知的环境变量配置！")
    else:
        check_stock()
