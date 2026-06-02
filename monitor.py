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
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.hmv.co.jp/"
}

def send_wx_notification(text):
    """通过 WxPusher 官方标准域名推送消息到微信"""
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
            
            # --- 【核心修复】智能识别网页编码 ---
            # 先尝试从响应头自动抓取编码，如果是 None 或者不准，再用 apparent_encoding 深度检测
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            # 如果深度检测还是乱码（HMV常见情况），这里给一个双重保险：直接尝试用日本本土的 Shift_JIS 解码
            try:
                # 尝试测试解码标题，如果含特殊文本导致失败，再回退
                test_soup = BeautifulSoup(response.content, 'html.parser')
                if test_soup.title and "" in test_soup.title.text:
                    response.encoding = 'shift_jis'
            except:
                pass

            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.text
            
            # 提取网页标题
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"抓取到的网页标题为: {title}")
            
            # 【严格正向匹配逻辑】
            is_buyable_button_present = "カートに入れる" in page_text
            
            if is_buyable_button_present:
                if "HMV" not in title and "" not in title:
                    print("警告：虽匹配到关键字，但网页标题异常（可能非HMV正常页面），跳过发送。")
                    continue
                    
                msg = f"🔔【HMV补货提醒】\n您监控的特价商品已确切放出了「加入购物车」按钮！请速度前往抢购！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 确认补货（成功匹配到购物车按钮），通知已发出！")
            else:
                print("检查结果：未检测到「カートに入れる」按钮。商品仍处于缺货状态或触发了防火墙。静默挂机中...")
                
        except Exception as e:
            print(f"请求商品页面出错: {e}")

if __name__ == "__main__":
    if not WX_APP_TOKEN or not WX_UID:
        print("错误：未检测到微信通知的环境变量配置！")
    else:
        check_stock()
