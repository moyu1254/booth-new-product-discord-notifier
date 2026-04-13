import json
import os
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

def load_config():
    """設定ファイル (config.json) を読み込む"""
    config_file = 'config.json'
    example_file = 'config.example.json'
    
    # config.jsonが存在しない場合
    if not os.path.exists(config_file):
        # config.example.jsonからコピーを試みる
        if os.path.exists(example_file):
            import shutil
            shutil.copy(example_file, config_file)
            print("📝 config.json が見つからなかったため、config.example.json からコピーしました")
            print("⚠️  config.json を編集して設定を行ってください")
        else:
            print("❌ エラー: config.json も config.example.json も見つかりません")
            return None
    
    # JSONファイルを開いて読み込む
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 環境変数からDiscord Webhook URLを取得（GitHub Actions用）
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if webhook_url:
        config['discord_webhook_url'] = webhook_url
        print("✅ 設定ファイルを読み込みました（環境変数からWebhook URL取得）")
    else:
        print("✅ 設定ファイルを読み込みました")
    
    return config


def load_seen_products():
    """既に通知した商品IDのリストを読み込む"""
    seen_file = 'seen_products.json'
    
    if os.path.exists(seen_file):
        with open(seen_file, 'r', encoding='utf-8') as f:
            seen = json.load(f)
        print(f"📋 既に通知済みの商品: {len(seen)}件")
        return seen
    else:
        print("📋 通知履歴ファイルを新規作成します")
        return []


def save_seen_products(seen_products):
    """既に通知した商品IDのリストを保存する"""
    seen_file = 'seen_products.json'
    
    with open(seen_file, 'w', encoding='utf-8') as f:
        json.dump(seen_products, f, ensure_ascii=False, indent=2)
    
    print(f"💾 通知履歴を保存しました ({len(seen_products)}件)")


def get_product_id_from_url(url):
    """
    商品URLから商品IDを抽���する
    
    Parameters:
        url (str): 商品URL（例: https://booth.pm/ja/items/8165985）
    
    Returns:
        str: 商品ID（例: "8165985"）
    """
    import re
    match = re.search(r'/items/(\d+)', url)
    if match:
        return match.group(1)
    return None


def send_discord_notification(webhook_url, product):
    """
    Discordに商品情報を通知する
    
    Parameters:
        webhook_url (str): Discord Webhook URL
        product (dict): 商品情報（title, url, price, image_url）
    """
    print(f"📢 Discordに通知中: {product['title']}")
    
    # Discord Embed形式でメッセージを作成
    embed = {
        "title": product['title'],
        "url": product['url'],
        "color": 16738740,  # オレンジ色
        "fields": [
            {
                "name": "価格",
                "value": product['price'],
                "inline": True
            }
        ],
        "thumbnail": {
            "url": product['image_url']
        },
        "footer": {
            "text": "BOOTH 新着通知"
        }
    }
    
    # Webhookに送信するデータ
    data = {
        "username": "BOOTH通知Bot",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        
        if response.status_code == 204:
            print("✅ Discord通知成功")
            return True
        else:
            print(f"⚠️ Discord通知失敗: ステータスコード {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Discord通知エラー: {e}")
        return False


def search_booth_products(tag):
    """
    Boothで指定されたタグの商品を検索する（Selenium使用）
    
    Parameters:
        tag (str): 検索するタグ（例: "ひかるん対応"）
    
    Returns:
        list: 商品情報のリスト
    """
    print(f"🔍 Boothで「{tag}」を検索中...")
    
    # 検索URL（新着順、adult=include）
    encoded_tag = urllib.parse.quote(tag)
    search_url = f"https://booth.pm/ja/items?adult=include&tags%5B%5D={encoded_tag}&sort=new"
    
    print(f"📍 URL: {search_url}")
    
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Chromeオプション設定（ヘッドレスモード）
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # バックグラウンドで実行
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')  # GitHub Actions用
    
    driver = None
    
    try:
        # Chromeブラウザを起動
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(search_url)
        
        print("⏳ ページの読み込み中...")
        
        # ページが読み込まれるまで待機（最大10秒）
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 年齢確認ページの「はい」ボタンをクリック
        try:
            print("🔞 年齢確認ページを確認中...")
            approve_button = driver.find_element(By.CLASS_NAME, "js-approve-adult")
            link = approve_button.find_element(By.TAG_NAME, "a")
            link.click()
            print("✅ 年齢確認完了")
            
            # ページが切り替わるまで待機
            time.sleep(3)
        except:
            print("⚠️ 年齢確認ページは表示されませんでした")
        
        print("📜 ページをスクロールして商品を読み込み中...")
        
        # ページを下にスクロール（遅延読み込み対応）
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # もう一度スクロール
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        print("✅ スクロール完了")
        
        # ページのHTMLを取得
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        print("✅ ページ取得成功")
        
        # 商品リストを格納
        products = []
        
        # 全てのリンクを取得
        all_links = soup.find_all('a', href=True)
        
        # 商品リンクを抽出（/items/ を含むもの）
        links = [link for link in all_links if '/items/' in link.get('href', '')]
        
        # さらに詳細にフィルタリング（商品ページのみ）
        # /items/数字 のパターンのみ
        import re
        product_links = []
        for link in links:
            href = link.get('href', '')
            # /items/数字 のパターンにマッチするか確認
            if re.search(r'/items/\d+', href):
                product_links.append(link)
        
        print(f"🎯 {len(product_links)}件の商品を発見")
        
        # product_linksを使用
        links = product_links
        
        for link in links[:5]:  # 最初の5件を取得
            try:
                url = link.get('href')
                if not url.startswith('http'):
                    url = 'https://booth.pm' + url
                
                # 親要素を探す（商品カード全体）
                card = link.find_parent('li')
                if not card:
                    card = link.find_parent('div')
                
                # タイトルを探す（複数のパターンを試す）
                title = None
                
                # パターン1: リンク内のテキスト
                if link.find('img'):
                    # 画像リンクの場合、alt属性を試す
                    img = link.find('img')
                    title = img.get('alt', '')
                
                # パターン2: 親要素内のタイトル要素
                if not title and card:
                    title_elem = card.find(['h2', 'h3', 'div'], class_=lambda x: x and 'title' in str(x).lower())
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                # パターン3: リンク自体のテキスト
                if not title:
                    title = link.get_text(strip=True)
                
                # 画像を探す
                image_url = ''
                if card:
                    img = card.find('img')
                    if img:
                        image_url = img.get('src', '') or img.get('data-src', '')
                
                # 価格を探す
                price = '価格不明'
                if card:
                    price_elem = card.find(['div', 'span'], class_=lambda x: x and 'price' in str(x).lower())
                    if price_elem:
                        price = price_elem.get_text(strip=True)
                
                if title and url and title != '':
                    product = {
                        'title': title,
                        'url': url,
                        'price': price,
                        'image_url': image_url
                    }
                    
                    products.append(product)
            
            except Exception as e:
                print(f"⚠️ エラー: {e}")
                continue
        
        return products
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return []
    
    finally:
        if driver:
            driver.quit()


def monitor_booth():
    """
    Boothを監視して新しい商品をDiscordに通知する
    """
    print("\n" + "="*50)
    print(f"🔄 監視開始: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    config = load_config()
    if not config:
        print("❌ 設定ファイルの読み込みに失敗しました")
        return
    
    # Discord Webhook URLが設定されているか確認
    webhook_url = config.get('discord_webhook_url', 'YOUR_DISCORD_WEBHOOK_URL_HERE')
    if webhook_url == 'YOUR_DISCORD_WEBHOOK_URL_HERE':
        print("\n⚠️ Discord Webhook URLが設定されていません")
        print("config.json の discord_webhook_url を設定してください")
        return
    
    # 既に通知した商品を読み込む
    seen_products = load_seen_products()
    
    # 各タグで検索
    for tag in config['booth_tags']:
        print(f"\n📌 タグ: {tag}")
        products = search_booth_products(tag)
        
        if not products:
            print(f"⚠️ 「{tag}」の商品が見つかりませんでした")
            continue
        
        print(f"✅ {len(products)}件の商品を取得しました")
        
        # 新しい商品のみ抽出
        new_products = []
        
        for product in products:
            product_id = get_product_id_from_url(product['url'])
            
            if product_id and product_id not in seen_products:
                new_products.append(product)
                seen_products.append(product_id)
        
        print(f"🆕 新しい商品: {len(new_products)}件")
        
        # 新しい商品をDiscordに通知
        for product in new_products:
            send_discord_notification(webhook_url, product)
            time.sleep(1)  # Discord API制限を避けるため1秒待機
        
        # タグ間で少し待機
        time.sleep(2)
    
    # 通知履歴を保存
    save_seen_products(seen_products)
    
    print("\n" + "="*50)
    print(f"✅ 監視完了: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)


# メイン実行
if __name__ == "__main__":
    import schedule
    
    # GitHub Actions環境かどうかを判定
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    if is_github_actions:
        # GitHub Actionsモード（自動実行）
        print("🤖 GitHub Actions モードで実行中")
        print("="*50)
        monitor_booth()
    else:
        # ローカル実行モード
        print("🚀 BOOTH Discord通知Bot 起動")
        print("="*50)
        
        config = load_config()
        if not config:
            print("❌ 設定ファイルの読み込みに失敗しました")
            exit(1)
        
        print(f"監視タグ: {config['booth_tags']}")
        print(f"チェック間隔: {config['check_interval_minutes']}分")
        
        # Discord Webhook URLが設定されているか確認
        webhook_url = config.get('discord_webhook_url', 'YOUR_DISCORD_WEBHOOK_URL_HERE')
        if webhook_url == 'YOUR_DISCORD_WEBHOOK_URL_HERE':
            print("\n⚠️ Discord Webhook URLが設定されていません")
            print("config.json の discord_webhook_url を設定してください")
            exit(1)
        
        print("\n起動モードを選択してください:")
        print("1. テスト実行（1回のみ）")
        print("2. 定期実行（設定された間隔で繰り返し）")
        
        mode = input("\n選択 (1 or 2): ").strip()
        
        if mode == "1":
            # テスト実行
            print("\n--- テスト実行モード ---")
            monitor_booth()
        
        elif mode == "2":
            # 定期実行
            print("\n--- 定期実行モード ---")
            print(f"⏰ {config['check_interval_minutes']}分ごとに監視を実行します")
            print("📢 Ctrl+C で停止できます\n")
            
            # 最初に1回実行
            monitor_booth()
            
            # スケジュール設定
            schedule.every(config['check_interval_minutes']).minutes.do(monitor_booth)
            
            # 無限ループで定期実行
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\n\n⏹️ Botを停止しました")
        
        else:
            print("❌ 無効な選択です")
            exit(1)