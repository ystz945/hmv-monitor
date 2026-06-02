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

# 使用标准的移动端 Headers，确保能拿到纯净且未被拦截的静态 HTML 源码
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
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
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"抓取到的网页标题为: {title}")
            
            # ==============================
            # 🚨 网页源代码【精准匹配双保险】
            # ==============================
            # 匹配特征 1：源码中是否存在 HMV 特有的“加入购物车”核心交互函数
            has_cart_js_func = "addcart" in html_content.lower()
            
            # 匹配特征 2：源码中是否存在专属于商品详情页的购买提交表单
            has_detail_form = soup.find("form", attrs={"name": "itemDetailForm"}) is not None
            
            # 匹配特征 3：源码中是否有用于改变购物车数量或直接购买的隐藏/实体交互元素
            has_cart_action = "cartaction" in html_content.lower() or "js-addcart" in html_content.lower()

            print(f"--- 源码硬核扫描结果 ---")
            print(f"  - 特征1 (包含addcart函数): {has_cart_js_func}")
            print(f"  - 特征2 (存在购买详情Form表单): {has_detail_form}")
            print(f"  - 特征3 (存在购物车Action指令): {has_cart_action}")
            print(f"------------------------")

            # 只要满足这三个底层源码核心特征的任意两个，就绝对代表当前商品“有购买通道”（即有货）
            match_score = sum([has_cart_js_func, has_detail_form, has_cart_action])
            is_buyable = match_score >= 2

            if is_buyable:
                # 标题安全过滤：防止误拦截正常 HMV 页面
                if "HMV" not in title and "未来日記" not in title:
                    print("警告：虽匹配到源码特征，但网页标题异常，跳过发送。")
                    continue
                    
                msg = f"🔔【HMV补货提醒】\n硬核源码扫描成功！您监控的商品已确切放出了购买通道！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 源码特征匹配成功，有货通知已发出！")
            else:
                print(f"检查结果：未通过源码特征匹配。当前累计后台运行次数: {current_count} 次。")
                
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
