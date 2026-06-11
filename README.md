# booth-new-product-discord-notifier

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-supported-2088FF?logo=githubactions&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-Webhook-5865F2?logo=discord&logoColor=white)

BOOTH の指定タグを検索し、新しく見つかった商品を Discord Webhook に通知する Python ツールです。

## 特徴

- 複数の BOOTH タグを監視できます。
- 通知済みの商品 ID を `seen_products.json` に保存し、重複通知を防ぎます。
- Discord の埋め込みメッセージに商品名、価格、タグ、商品 URL、サムネイルを表示します。
- GitHub Actions で 30 分ごとの自動実行ができます。
- Windows 向け exe を GitHub Actions でビルドできます。

## 必要環境

| 項目 | 内容 |
| --- | --- |
| Python | 3.11 |
| 主要ライブラリ | `requests`, `beautifulsoup4` |
| 通知先 | Discord Webhook URL |

## 使い方

### GitHub Actions で定期実行する

1. このリポジトリをフォークします。
2. `config.example.json` を `config.json` にコピーし、`booth_tags` を編集します。
3. Repository secrets に `DISCORD_WEBHOOK_URL` を登録します。
4. `Actions` タブで `BOOTH Monitor` を有効化します。

`BOOTH Monitor` は `.github/workflows/monitor.yml` により 30 分ごとに実行されます。手動実行もできます。

### ローカルで実行する

```bash
pip install -r requirements.txt
cp config.example.json config.json
python main.py
```

`python main.py` は 1 回だけチェックして終了します。継続的に使う場合は、OS のタスクスケジューラや cron で定期実行してください。

### Windows exe を使う

[Releases](https://github.com/moyu1254/booth-new-product-discord-notifier/releases) から `booth-notifier-windows.zip` をダウンロードし、展開して実行します。

```text
booth-notifier.exe
```

同じフォルダにある `config.json` を編集してから起動してください。

## 設定

`config.json` の例です。

```json
{
  "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL_HERE",
  "booth_tags": ["監視したいタグ名"],
  "check_interval_minutes": 30,
  "booth_search_url": "https://booth.pm/ja/search"
}
```

| キー | 内容 |
| --- | --- |
| `discord_webhook_url` | Discord Webhook URL。`DISCORD_WEBHOOK_URL` がある場合は環境変数が優先されます。 |
| `booth_tags` | 監視する BOOTH タグの配列です。 |
| `check_interval_minutes` | 実行間隔の設定値です。GitHub Actions の実行間隔は `monitor.yml` の cron で管理します。 |
| `booth_search_url` | 検索 URL の設定値です。 |

GitHub Actions で使う場合、Webhook URL は `config.json` に直接書かず、Repository secrets の `DISCORD_WEBHOOK_URL` に登録してください。

## ディレクトリ構成

```text
.
├── .github/
│   └── workflows/
│       ├── build-release.yml
│       └── monitor.yml
├── config.example.json
├── main.py
├── README.md
└── requirements.txt
```

| パス | 内容 |
| --- | --- |
| `main.py` | BOOTH 商品取得、重複判定、Discord 通知を行います。 |
| `config.example.json` | 設定ファイルのサンプルです。 |
| `.github/workflows/monitor.yml` | 30 分ごとの自動実行ワークフローです。 |
| `.github/workflows/build-release.yml` | Windows exe のビルドとリリース作成を行います。 |
| `seen_products.json` | 通知済みの商品 ID を保存します。初回実行時に作成されます。 |

## コマンド

| コマンド | 内容 |
| --- | --- |
| `pip install -r requirements.txt` | 依存ライブラリをインストールします。 |
| `python main.py` | BOOTH をチェックして新商品を通知します。 |
| `pyinstaller --onefile --name booth-notifier main.py` | Windows 向け exe を作成します。 |

## トラブルシューティング

### `config.json not found.` と表示される

`config.example.json` を `config.json` にコピーしてください。

### `Invalid config or missing Webhook URL.` と表示される

`discord_webhook_url` または `DISCORD_WEBHOOK_URL` を設定してください。

### 通知が届かない

Discord Webhook URL が正しいか確認してください。すでに `seen_products.json` に保存されている商品は再通知されません。

### GitHub Actions で `git push` が失敗する

Repository settings の Actions 権限で `Read and write permissions` を有効にしてください。`seen_products.json` のコミットに必要です。
