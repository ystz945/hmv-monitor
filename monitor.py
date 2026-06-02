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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.hmv.co.jp/",
    "Cache-Control": "no-cache"
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

def check_stock(current_count):
    for url in URLS:
        try:
            print(f"正在请求网页并准备导出源码: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"网页请求失败，状态码: {response.status_code}")
                continue
            
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            html_content = response.text
            
            # ===== 🚨 【核心功能：保存完整网页到本地文件】 =====
            output_filename = "downloaded_page.html"
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"✨ 成功！完整的网页源码已写入本地文件: {output_filename} (共 {len(html_content)} 字节)")
            # =================================================
            
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.text
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"当前抓取到的网页标题: {title}")
            print(f"检查结果：网页已成功导出。当前累计后台运行次数: {current_count} 次。")
                
        except Exception as e:
            print(f"请求商品页面或保存文件出错: {e}")

if __name__ == "__main__":
    current_count = get_and_update_count()
    check_stock(current_count)
