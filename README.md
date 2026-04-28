# SNS投稿案 Gmail送信ツール

Claude Codeで生成したSNS投稿案を、Gmailで自分宛に送信して確認するためのツールです。

## ファイル構成

```
habit-tracker/
  posts.csv                 # SNS投稿データ（CSVフォーマット）
  content_calendar.json     # SNS投稿データ（JSONフォーマット）
  send_to_gmail.py          # Gmail送信スクリプト（メイン）
  .env.example              # 環境変数のテンプレート
  .env                      # 実際の認証情報（Git管理外・要作成）
  requirements.txt          # 必要なPythonライブラリ
  README.md                 # このファイル
```

---

## セットアップ手順

### 1. Gmailアプリパスワードの取得

通常のGoogleパスワードは使用できません。「**アプリパスワード**」が必要です。

1. [Googleアカウント](https://myaccount.google.com/) にアクセス
2. 左メニューの「**セキュリティ**」をクリック
3. 「**2段階認証プロセス**」を有効にする（まだの場合）
4. 2段階認証のページ下部にある「**アプリパスワード**」をクリック
5. アプリ名に任意の名前（例: `SNS投稿送信`）を入力して「作成」
6. 表示される **16文字のパスワード** をメモする（スペースなしで使用）

### 2. .env ファイルの作成

`.env.example` をコピーして `.env` を作成します。

```bash
cp .env.example .env
```

`.env` を開いて、取得した情報を入力してください。

```
GMAIL_USER=あなたのGmailアドレス@gmail.com
GMAIL_APP_PASSWORD=取得した16文字のアプリパスワード
TO_EMAIL=送信先のメールアドレス（自分宛なら上と同じ）
```

**注意**: `.env` は絶対にGitにコミットしないでください。`.gitignore` で除外済みです。

### 3. 必要ライブラリのインストール

```bash
pip install -r requirements.txt
```

---

## 実行コマンド

```bash
python send_to_gmail.py
```

実行すると以下の処理が行われます。

1. `posts.csv`（なければ `content_calendar.json`）を読み込む
2. `status=draft` かつ薬機法チェック済みの投稿を抽出
3. 整形したメールを自分宛に送信
4. 送信成功した投稿の `status` を `sent_to_gmail` に更新

---

## 送信対象の条件

以下の **すべて** を満たす投稿のみ送信されます。

| 条件 | 説明 |
|------|------|
| `status = draft` | 下書き状態の投稿 |
| `body` が空でない | 本文があること |
| `risk_check` に「安全」または「問題なし」を含む | 薬機法リスクチェック済み |

---

## データファイルのフォーマット

### posts.csv（優先）

```csv
id,category,title,body,target,scientific_basis,risk_check,platform,status,created_at,sent_at
1,朝活,タイトル,本文,ターゲット,科学的根拠,安全：理由,Instagram,draft,2026-04-01 08:00:00,
```

### content_calendar.json

```json
{
  "posts": [
    {
      "id": 1,
      "category": "朝活",
      "title": "タイトル",
      "body": "本文",
      "target": "ターゲット",
      "scientific_basis": "科学的根拠",
      "risk_check": "安全：理由",
      "platform": "Instagram",
      "status": "draft",
      "created_at": "2026-04-01 08:00:00",
      "sent_at": null
    }
  ]
}
```

---

## 送信できない時の確認ポイント

### 「Gmail 認証に失敗しました」

- `.env` の `GMAIL_USER` が正しいGmailアドレスか確認
- `GMAIL_APP_PASSWORD` が**アプリパスワード**（16文字）か確認
  - 通常のGoogleパスワードは使えません
  - スペースは入れないでください
- Googleアカウントで**2段階認証が有効**になっているか確認

### 「送信対象の投稿がありません」

- `posts.csv` または `content_calendar.json` の `status` が `draft` になっているか確認
- `risk_check` の値に「安全」または「問題なし」が含まれているか確認
- `body`（本文）が空になっていないか確認

### 「posts.csv も content_calendar.json も見つかりません」

- スクリプトと同じディレクトリにファイルがあるか確認
- スクリプトをプロジェクトルートから実行しているか確認

### 「python-dotenv がインストールされていません」

```bash
pip install python-dotenv
```

### メールは届いているのに文字化けしている

- メールクライアントの文字コードを UTF-8 に設定してください

---

## セキュリティについて

- APIキーやパスワードはコード内に書かず、必ず `.env` に保存してください
- `.env` は `.gitignore` で除外済みのため、Gitにコミットされません
- `.env.example` には実際の値を入れず、テンプレートとしてのみ使用してください
