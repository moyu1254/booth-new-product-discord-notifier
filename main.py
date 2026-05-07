import json
import os
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup

# --- 設定管理 ---
def load_config():
    path = 'config.json'
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        return None

    with open(path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 環境変数があれば優先
    config['discord_webhook_url'] = os.environ.get('DISCORD_WEBHOOK_URL', config.get('discord_webhook_url'))
    return config

def load_seen_products():
    path = 'seen_products.json'
    if not os.path.exists(path):
        return set()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()

def save_seen_products(seen_products):
    with open('seen_products.json', 'w', encoding='utf-8') as f:
        json.dump(list(seen_products), f, ensure_ascii=False, indent=2)

# --- ユーティリティ ---
def get_product_id(url):
    match = re.search(r'/items/(\d+)', url)
    return match.group(1) if match else None

def clean_text(text):
    return re.sub(r'\s+', ' ', text or '').strip()

# --- スクレイピングロジック ---
def parse_product_card(card):
    """
    商品カード(li要素など)からタイトル、価格、URL、画像URLを抽出
    """
    # タイトルとリンクの取得
    link_elem = card.find('a', href=True, class_=re.compile(r'item-card__title|pc--item-card__title'))
    if not link_elem:
        link_elem = card.find('a', href=True)
    
    if not link_elem:
        return None

    href = link_elem.get('href', '')
    product_id = get_product_id(href)
    if not product_id:
        return None

    # タイトル抽出
    title = clean_text(link_elem.get_text())
    if not title:
        img = card.find('img')
        title = clean_text(img.get('alt')) if img else "無題の商品"

    # 価格抽出
    price_elem = card.find('div', class_=re.compile(r'price'))
    price = clean_text(price_elem.get_text()) if price_elem else "価格不明"

    # 画像URL抽出
    img_elem = card.find('img')
    image_url = ""
    if img_elem:
        # Lazy load対策でdata-srcなども確認
        image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-original') or ""
        if image_url.startswith('//'):
            image_url = 'https:' + image_url

    return {
        'id': product_id,
        'title': title,
        'url': f'https://booth.pm/ja/items/{product_id}',
        'price': price,
        'image_url': image_url
    }

def fetch_products_by_tag(session, tag):
    encoded_tag = urllib.parse.quote(tag)
    # 成人向けを含む設定をURLパラメータで付与
    url = f'https://booth.pm/ja/items?adult=include&tags%5B%5D={encoded_tag}&sort=new'
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 商品カードを抽出
        cards = soup.find_all(['li', 'div'], class_=re.compile(r'item-card'))
        
        products = []
        for c in cards:
            p = parse_product_card(c)
            if p:
                products.append(p)
        return products
    except Exception as e:
        print(f"Error fetching tag {tag}: {e}")
        return []

# --- 通知 ---
def send_discord(webhook_url, product, tag):
    embed = {
        'title': product['title'][:256],
        'url': product['url'],
        'color': 0xFF6FAE,
        'fields': [
            {'name': '価格', 'value': product['price'][:1024], 'inline': True},
            {'name': 'タグ', 'value': tag[:1024], 'inline': True},
        ],
        'footer': {'text': 'BOOTH Monitor'}
    }
    if product['image_url']:
        embed['thumbnail'] = {'url': product['image_url']}

    try:
        res = requests.post(webhook_url, json={'username': 'BOOTH通知Bot', 'embeds': [embed]}, timeout=10)
        return res.status_code == 204
    except Exception:
        return False

# --- メイン処理 ---
def main():
    config = load_config()
    if not config or not config.get('discord_webhook_url'):
        print("Invalid config or missing Webhook URL.")
        return

    webhook_url = config['discord_webhook_url']
    if webhook_url == 'YOUR_DISCORD_WEBHOOK_URL_HERE':
        print("Please set your Discord Webhook URL in config.json or environment variable.")
        return

    seen_ids = load_seen_products()
    new_seen_count = 0

    with requests.Session() as session:
        for tag in config.get('booth_tags', []):
            print(f"Checking tag: {tag}")
            products = fetch_products_by_tag(session, tag)
            
            # 見つかった商品のうち、未通知のもののみ処理
            for p in products:
                if p['id'] not in seen_ids:
                    if send_discord(webhook_url, p, tag):
                        seen_ids.add(p['id'])
                        new_seen_count += 1
                        time.sleep(1) # Discordのレートリミット回避
            
            time.sleep(2) # BOOTHサーバーへの負荷軽減

    if new_seen_count > 0:
        save_seen_products(seen_ids)
        print(f"Done. {new_seen_count} new products notified.")
    else:
        print("No new products.")

if __name__ == '__main__':
    main()
