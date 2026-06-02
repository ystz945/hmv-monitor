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
    # 换用更现代的 Mac Chrome 浏览器 User-Agent 伪装，降低被机房防火墙直接拦截的概率
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
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.text
            
            # --- 增加调试输出：看看 GitHub 服务器实际抓到了什么页面 ---
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"抓取到的网页标题为: {title}")
            
            # 【终极防误报核心逻辑】：严格的正向匹配
            # 不再关心页面里有没有“注文不可”。
            # 哪怕请求返回了人机验证码页面、拦截页、或者网页残缺，只要页面里没有确确实实出现“カートに入れる”（加入购物车）这个按钮文本，就绝对不报警！
            is_buyable_button_present = "カートに入れる" in page_text
            
            if is_buyable_button_present:
                # 双重保险：确保页面确实是 HMV 的商品页，而不是某个标题带有对应文字的异常页面
                if "HMV" not in title:
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
