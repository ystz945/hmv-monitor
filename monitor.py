import os
import requests
import re
from bs4 import BeautifulSoup

# ==================== 配置区 ====================
URLS = [
    "https://www.hmv.co.jp/artist_South-Club_000000000718535/item_2nd-EP-20_8866649"
]
COUNTER_FILE = ".monitor_counter.txt"
# ================================================

WX_APP_TOKEN = os.getenv("WX_APP_TOKEN")
WX_UID = os.getenv("WX_UID")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.hmv.co.jp/",
    "Cache-Control": "no-cache"
}

def get_and_update_count():
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
            print(f"正在读取商品底层静态元数据: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"网页请求失败，状态码: {response.status_code}")
                continue
            
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.text.strip() if soup.title else "无标题"
            
            # 🚨 核心逻辑：利用正则表达式从源码的 JS 变量中精准提取购物车按钮状态
            # 匹配 "cartBtnDispFlg" : "1" 或 "cartBtnDispFlg":"1"
            cart_flag_match = re.search(r'"cartBtnDispFlg"\s*:\s*"([^"]+)"', html_content)
            stock_status_match = re.search(r'"stockStatus"\s*:\s*"([^"]+)"', html_content)
            
            cart_disp_flg = cart_flag_match.group(1) if cart_flag_match else "未找到"
            stock_status = stock_status_match.group(1) if stock_status_match else "未找到"
            
            print("--- HMV 核心元数据解密面板 ---")
            print(f"  - 网页标题: {title}")
            print(f"  - 购物车按钮渲染状态 (cartBtnDispFlg): {cart_disp_flg}")
            print(f"  - 底层系统库存状态码 (stockStatus): {stock_status}")
            print("------------------------------")
            
            # 【终极判定标准】：
            # 只要静态源码里的 cartBtnDispFlg 的值明确等于 "1"，说明哪怕前端还在转圈，系统也已经开放了购买通道！
            if cart_disp_flg == "1":
                if "HMV" not in title and "未来日記" not in title:
                    print("警告：数据虽匹配，但网页标题异常，判定为非商品页，跳过。")
                    continue
                    
                msg = f"🔔【HMV补货提醒】\n底层数据流校验成功！系统已将该商品标记为『可购买』状态！\n\n商品：{title}\n链接：{url}"
                send_wx_notification(msg)
                print("💥 成功锁定核心元数据！有货通知已发出！")
            else:
                print(f"检查结果：元数据标志显示目前无法购买。当前累计运行: {current_count} 次。")
                
                # 每 6 小时发送一次运行简报
                if current_count % 36 == 0:
                    report_msg = f"🤖【HMV监控运行简报】\n数据层监控系统已平稳运行 6 小时。\n当前累计安全运行次数：{current_count} 次。\n状态：商品 cartBtnDispFlg={cart_disp_flg}，继续静默站岗中。"
                    print("📊 达到 6 小时周期，正在发送运行次数日志...")
                    send_wx_notification(report_msg)
                
        except Exception as e:
            print(f"请求处理出错: {e}")

if __name__ == "__main__":
    if not WX_APP_TOKEN or not WX_UID:
        print("错误：未检测到微信通知的环境变量配置！")
    else:
        current_count = get_and_update_count()
        check_stock(current_count)
