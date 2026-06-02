def check_stock():
    for url in URLS:
        try:
            print(f"正在检查商品: {url}")
            # 换一个更现代的 Mac 浏览器 User-Agent 伪装
            headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"网页请求失败，状态码: {response.status_code}，本次跳过。")
                continue
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.text
            
            # --- 增加调试输出：看看服务器到底给我们返回了什么页面 ---
            title = soup.title.text.strip() if soup.title else "无标题"
            print(f"抓取到的网页标题为: {title}")
            
            # 【终极防误报逻辑】：严格的正向匹配
            # 彻底抛弃反向查找“注文不可”的逻辑。
            # 哪怕被拦截、哪怕页面残缺，只要没确确实实看到“カートに入れる”（加入购物车），就不报警！
            is_buyable_button_present = "カートに入れる" in page_text
            
            if is_buyable_button_present:
                msg = f"🔔【HMV补货提醒】\n您监控的特价商品确切放出了「加入购物车」按钮！请速去抢购！\n\n链接：{url}"
                send_wx_notification(msg)
                print("💥 确认补货（发现加入购物车按钮），通知已发出！")
            else:
                print("检查结果：未检测到「カートに入れる」按钮。可能缺货或触发了反爬策略。静默挂机中...")
                
        except Exception as e:
            print(f"请求商品页面出错: {e}")
