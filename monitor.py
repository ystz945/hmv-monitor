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
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.hmv.co.jp/"
}

def send_wx_notification(text):
    """通过 WxPusher 官方新域名推送消息到微信"""
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

def check_stock():
    for url in URLS:
        try:
            print(f"正在检查商品: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"网页请求失败，状态码: {response.status_code}，本次跳过。")
                continue
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.text
            
            # 【核心逻辑升级】：改用“有货特征”来精准判定
            # 当 HMV 补货时，右侧一定会放出红色按钮“カートに入れる” (加入购物车)
            # 同时，原本无货的提示 “現在オンラインでご注文いただけません” 会消失
            is_buyable_button_present = "カートに入れる" in page_text
            is_out_of_stock_text_present = "現在オンラインでご注文いただけません" in page_text
            
            # 安全触发阀门：只有当【发现了加入购物车按钮】或者【断货文字彻底消失】时，才发送通知
            if is_buyable_button_present or (not is_out_of_stock_text_present and "注文不可" not in page_text):
                # 再次过滤掉因海外 IP 被彻底拦截（如返回完全空白页或错误页）导致的误报
                if "HMV" not in soup.title.text if soup.title else True:
                    print("检测到异常页面（可能是IP被拦截），跳过发送以防误报。")
                    continue
                    
                msg = f"🔔【HMV补货提醒】\n您监控的特价商品可能恢复库存（放出了加入购物车按钮）！请速度查看！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 确认补货，通知已发出！")
            else:
                print("检查结果：依旧处于『注文不可』，未检测到购物车按钮。静默挂机中...")
                
        except Exception as e:
            print(f"请求商品页面出错: {e}")

if __name__ == "__main__":
    if not WX_APP_TOKEN or not WX_UID:
        print("错误：未检测到微信通知的环境变量配置！")
    else:
        check_stock()
