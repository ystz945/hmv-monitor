import os
import requests
import json

# ==================== 配置区 ====================
# 【重要】：监控时请确保这里的 URL 格式包含完整的 item_商品名_商品ID
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
            # 从传统的商品 URL 中精准提取 HMV 的唯一商品 7 位或 10 位数字 ID
            # 例如从 ..._8866649 中提取出 8866649
            product_id = url.split("_")[-1]
            print(f"正在通过官方 API 接口穿透检查商品 ID: {product_id}")
            
            # 构造 HMV 官方异步无拦截库存查询端点
            api_url = f"https://www.hmv.co.jp/multisite/action/stocks?itemIds={product_id}"
            
            response = requests.get(api_url, headers=headers, timeout=15)
            
            print(f"--- API 原始响应诊断 ---")
            print(f"状态码: {response.status_code}")
            raw_text = response.text.strip()
            print(f"接口返回内容摘要: {raw_text[:200]}")
            print(f"------------------------")

            if response.status_code != 200:
                print("接口请求异常，本次跳过。")
                continue

            # 核心逻辑：接口如果不返回包含“断货/不能购买”的特定缺货代码，或者检测到库存数改变
            # HMV 缺货在无拦截接口中通常表现为数量为0或特定状态码
            is_out_of_stock = "outOfStock" in raw_text or '"stock":0' in raw_text.replace(" ", "") or "注文不可" in raw_text
            
            # 反之，若接口正常响应，且里面明确包含了该商品ID，同时没有缺货关键字，即为有货
            if product_id in raw_text and not is_out_of_stock:
                msg = f"🔔【HMV补货提醒】\nAPI 接口穿透成功！您监控的商品已确切释放库存，处于可购买状态！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 API 状态判定有货，通知已发出！")
            else:
                print(f"检查结果：API 返回显示当前仍处于无货或锁定状态。当前累计运行次数: {current_count} 次。")
                
                # 每 6 小时发送一次运行简报
                if current_count % 36 == 0:
                    report_msg = f"🤖【HMV监控运行简报】\nAPI 盯梢系统已持续为您守护 6 小时。\n当前累计安全运行次数：{current_count} 次。\n监控商品依旧无货，系统继续静默站岗中。"
                    print("📊 达到 6 小时周期，正在发送运行次数日志...")
                    send_wx_notification(report_msg)
                
        except Exception as e:
            print(f"请求商品 API 异常: {e}")

if __name__ == "__main__":
    if not WX_APP_TOKEN or not WX_UID:
        print("错误：未检测到微信通知的环境变量配置！")
    else:
        current_count = get_and_update_count()
        check_stock(current_count)
