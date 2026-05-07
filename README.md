# booth-new-product-discord-notifier

Boothの特定のタグの新商品をDiscordに通知するツール

## 使い方

### 🖥️ ソフトウェア版（.exe）

1. [Releases](https://github.com/moyukiti1254-web/booth-new-product-discord-notifier/releases) から `booth-notifier-windows.zip` をダウンロードする
2. zip を展開する
3. `config.json` を編集する
   - `booth_tags`: 監視したいBoothのタグ名を設定する
   - `discord_webhook_url`: DiscordのWebhook URLを設定する
4. `booth-notifier.exe` をダブルクリックして起動する

> 💡 今回のアップデートにより、**Google Chromeのインストールは不要**になりました。

### ☁️ GitHub Actions 版（自動定期実行）

1. このリポジトリをフォークまたはクローンする
2. `config.example.json` を `config.json` にコピーして編集する
   - `booth_tags`: 監視したいBoothのタグ名を設定する
   - `check_interval_minutes`: チェック間隔（分）を設定する
3. GitHub の Secrets に `DISCORD_WEBHOOK_URL` を登録する
   - リポジトリの Settings → Secrets and variables → Actions → New repository secret
   - Name: `DISCORD_WEBHOOK_URL`、Value: DiscordのWebhook URL
4. GitHub Actions が自動で定期実行される（デフォルト: 30分ごと）

## 設定

### config.json

| キー | 説明 | 例 |
|---|---|---|
| `booth_tags` | 監視するBoothのタグ名（複数可） | `["タグA", "タグB"]` |
| `check_interval_minutes` | チェック間隔（分） | `30` |
| `discord_webhook_url` | DiscordのWebhook URL（ソフトウェア版） | `"https://discord.com/api/webhooks/..."` |

### GitHub Secrets

| Secret名 | 説明 |
|---|---|
| `DISCORD_WEBHOOK_URL` | DiscordのWebhook URL（GitHub Actions版） |

## 必要環境

- Python 3.11+
- (ブラウザのインストールは不要です)

## ローカルでの実行

```bash
pip install -r requirements.txt
cp config.example.json config.json
# config.json を編集してから実行
python main.py
