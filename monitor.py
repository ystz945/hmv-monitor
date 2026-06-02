import os
import requests
import json

# ==================== 配置区 ====================
# 目前放的是您用来测试的有货商品链接
URLS = [
    "https://www.hmv.co.jp/artist_South-Club_000000000718535/item_2nd-EP-20_8866649"
]
COUNTER_FILE = ".monitor_counter.txt"
# ================================================

WX_APP_TOKEN = os.getenv("WX_APP_TOKEN")
WX_UID = os.getenv("WX_UID")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.hmv.co.jp/",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
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
    # 使用会话 Session 自动保持和继承网页的 Cookie 状态
    session = requests.Session()
    
    for url in URLS:
        try:
            product_id = url.split("_")[-1]
            print(f"第一步：正在访问商品网页以建立会话环境: {url}")
            
            # 先请求一次网页，让 session 拿到基础网络凭证
            page_res = session.get(url, headers=headers, timeout=15)
            print(f"网页访问状态: {page_res.status_code}，已成功获取并同步浏览器会话环境。")
            
            # 第二步：构造内部动态库存接口（加入 cache-busting 随机数防止被机房缓存骗过）
            api_url = f"https://www.hmv.co.jp/multisite/action/stocks?itemIds={product_id}"
            print(f"第二步：使用同会话穿透刺探动态库存接口: {api_url}")
            
            api_res = session.get(api_url, headers=headers, timeout=15)
            
            print("==================================================")
            print(f"🚨 【内部接口返回的原始状态流】状态码: {api_res.status_code}")
            raw_text = api_res.text.strip()
            print(f"内容明文: {raw_text}")
            print("==================================================")
            
            if api_res.status_code != 200 or not raw_text:
                print("核心接口未正确吐出数据，本次跳过。")
                continue

            # 3. 【无货与有货的核心判定硬核标准】
            # 在后台数据流中，只要出现以下任何一个断货词，就代表【绝对无货】
            # 如果没有这些词，并且返回的数据里有该商品ID，则说明【绝对有货】
            is_out_of_stock = (
                "outOfStock" in raw_text or 
                '"stock":0' in raw_text.replace(" ", "") or 
                "注文不可" in raw_text or
                "販売終了" in raw_text
            )
            
            if product_id in raw_text and not is_out_of_stock:
                msg = f"🔔【HMV补货提醒】\n底层数据流穿透成功！您监控的商品已确切放出了购买通道（无断货拦截）！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 接口扫描成功，确认有货，通知已发出！")
            else:
                print(f"检查结果：数据流中明确检测到断货词或库存为0。当前累计运行次数: {current_count} 次。")
                
                # 每 6 小时发送一次运行简报
                if current_count % 36 == 0:
                    report_msg = f"🤖【HMV监控运行简报】\nAPI 穿透盯梢系统已持续为您守护 6 小时。\n当前累计安全运行次数：{current_count} 次。\n监控商品处于缺货状态，继续静默站岗中。"
                    print("📊 达到 6 小时周期，正在发送运行次数日志...")
                    send_wx_notification(report_msg)
                
        except Exception as e:
            print(f"请求商品动态数据出错: {e}")

if __name__ == "__main__":
    if not WX_APP_TOKEN or not WX_UID:
        print("错误：未检测到微信通知的环境变量配置！")
    else:
        current_count = get_and_update_count()
        check_stock(current_count)
