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

# 使用最稳妥的电脑端 Header，保证拿到最全的 5900+ 字网页骨架
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
            print(f"正在精准解剖静态源码: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"网页请求失败，状态码: {response.status_code}")
                continue
            
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"抓取到的网页标题为: {title}")
            
            # ==========================================
            # 🚨 终极漏洞扫描：全网页底层 HTML 核心代码分析
            # ==========================================
            # 特征 1：寻找页面源码中是否存在任何形式的购物车类名或图标属性（有货时全页必有）
            has_cart_class = "cart-btn" in html_content or "icon-cart" in html_content or "btn_cart" in html_content
            
            # 特征 2：寻找页面源码中是否存在 HMV 特有的绝对无货/断货死锁词
            # "販売を終了" (结束贩卖) / "お取り扱いできません" (无法处理) / "注文不可"
            is_dead_product = "販売を終了" in html_content or "お取り扱いできません" in html_content
            
            print("--- 源码深度解剖诊断 ---")
            print(f"  - 源码内是否存在购物车组件特征: {has_cart_class}")
            print(f"  - 源码内是否存在绝对断货词拦截: {is_dead_product}")
            print("------------------------")

            # 核心匹配逻辑：只要源码中包含购物组件类，且【完全没有】绝对断货死锁词，即判定有货！
            if has_cart_class and not is_dead_product:
                if "HMV" not in title and "未来日記" not in title:
                    print("警告：虽通过源码判定，但网页标题异常，跳过发送。")
                    continue
                    
                msg = f"🔔【HMV补货提醒】\n静态源码漏洞判定成功！您监控的商品已确切有货！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 源码精准匹配成功，有货通知已发出！")
            else:
                print(f"检查结果：源码判定当前处于断货状态。当前累计后台运行次数: {current_count} 次。")
                
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
