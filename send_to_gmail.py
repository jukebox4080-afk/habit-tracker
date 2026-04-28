#!/usr/bin/env python3
"""SNS投稿案をGmailで自分宛に送信するスクリプト"""

import csv
import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("エラー: python-dotenv がインストールされていません。")
    print("  pip install python-dotenv  を実行してください。")
    sys.exit(1)

# ── 定数 ─────────────────────────────────────────────
CSV_FILE = Path("posts.csv")
JSON_FILE = Path("content_calendar.json")
SUBJECT = "【SNS投稿案】朝活・健康投稿案の確認"
SAFE_KEYWORDS = ["安全", "問題なし"]
DRAFT_STATUS = "draft"
SENT_STATUS = "sent_to_gmail"

# ── 環境変数の読み込み ────────────────────────────────
def load_env() -> tuple[str, str, str]:
    """
    .env から Gmail 認証情報を読み込む。
    必須キーが欠けている場合は終了する。
    """
    load_dotenv()
    gmail_user = os.getenv("GMAIL_USER", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    to_email = os.getenv("TO_EMAIL", "").strip()

    missing = []
    if not gmail_user:
        missing.append("GMAIL_USER")
    if not app_password:
        missing.append("GMAIL_APP_PASSWORD")
    if not to_email:
        missing.append("TO_EMAIL")

    if missing:
        print("エラー: .env に以下の設定が見つかりません:")
        for key in missing:
            print(f"  - {key}")
        print("\n.env.example を参考に .env ファイルを作成してください。")
        sys.exit(1)

    return gmail_user, app_password, to_email


# ── データ読み込み ─────────────────────────────────────
def load_posts() -> tuple[list[dict], str]:
    """
    posts.csv または content_calendar.json からデータを読み込む。
    両方存在する場合は posts.csv を優先。
    戻り値: (投稿リスト, ソースファイルのパス文字列)
    """
    if CSV_FILE.exists():
        return _load_csv(), str(CSV_FILE)
    if JSON_FILE.exists():
        return _load_json(), str(JSON_FILE)

    print("エラー: posts.csv も content_calendar.json も見つかりません。")
    print("  どちらかのファイルをプロジェクトルートに配置してください。")
    sys.exit(1)


def _load_csv() -> list[dict]:
    posts = []
    try:
        with open(CSV_FILE, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required = {"id", "status", "body", "risk_check"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                print(f"エラー: posts.csv に必須カラムがありません: {missing}")
                sys.exit(1)
            for row in reader:
                posts.append(dict(row))
    except csv.Error as e:
        print(f"エラー: posts.csv の形式が不正です: {e}")
        sys.exit(1)
    return posts


def _load_json() -> list[dict]:
    try:
        with open(JSON_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"エラー: content_calendar.json の形式が不正です: {e}")
        sys.exit(1)

    if isinstance(data, dict) and "posts" in data:
        return data["posts"]
    if isinstance(data, list):
        return data

    print("エラー: content_calendar.json の構造が不正です。")
    print('  {"posts": [...]} または [...] の形式で記述してください。')
    sys.exit(1)


# ── 送信対象のフィルタリング ──────────────────────────
def filter_posts(posts: list[dict]) -> list[dict]:
    """
    以下の条件をすべて満たす投稿のみ返す:
      - status が draft
      - body が空でない
      - risk_check に「安全」または「問題なし」が含まれる
    """
    targets = []
    for post in posts:
        status = str(post.get("status", "")).strip()
        body = str(post.get("body", "")).strip()
        risk = str(post.get("risk_check", "")).strip()

        if status != DRAFT_STATUS:
            continue
        if not body:
            continue
        if not any(kw in risk for kw in SAFE_KEYWORDS):
            continue

        targets.append(post)

    return targets


# ── メール本文の作成 ──────────────────────────────────
def build_email_body(posts: list[dict]) -> str:
    """投稿リストを読みやすいプレーンテキストに整形する"""
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    lines = [
        f"SNS投稿案 確認メール",
        f"送信日時: {now_str}",
        f"送信対象件数: {len(posts)} 件",
        "",
        "=" * 60,
        "",
    ]

    for i, post in enumerate(posts, start=1):
        lines += [
            f"■ 投稿 {i} / {len(posts)}",
            f"  投稿番号          : {post.get('id', 'N/A')}",
            f"  カテゴリ          : {post.get('category', 'N/A')}",
            f"  タイトル          : {post.get('title', 'N/A')}",
            "",
            "  【本文】",
        ]
        for body_line in str(post.get("body", "")).splitlines():
            lines.append(f"  {body_line}")
        lines += [
            "",
            f"  ターゲット        : {post.get('target', 'N/A')}",
            f"  科学的根拠の方向性: {post.get('scientific_basis', 'N/A')}",
            f"  薬機法リスクチェック: {post.get('risk_check', 'N/A')}",
            f"  投稿予定プラットフォーム: {post.get('platform', 'N/A')}",
            "",
            "-" * 60,
            "",
        ]

    lines.append("このメールはSNS投稿案確認システムにより自動送信されました。")
    return "\n".join(lines)


# ── Gmail 送信 ────────────────────────────────────────
def send_gmail(gmail_user: str, app_password: str, to_email: str, body: str):
    """smtplib で Gmail SMTP (TLS) 経由でメールを送信する"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = gmail_user
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_user, app_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        print("エラー: Gmail 認証に失敗しました。")
        print("  ・GMAIL_USER が正しいメールアドレスか確認してください。")
        print("  ・GMAIL_APP_PASSWORD はアプリパスワード（16文字）を使用してください。")
        print("  ・通常のGoogleアカウントパスワードは使用できません。")
        sys.exit(1)
    except smtplib.SMTPException as e:
        print(f"エラー: Gmail 送信に失敗しました: {e}")
        sys.exit(1)
    except TimeoutError:
        print("エラー: Gmail サーバーへの接続がタイムアウトしました。")
        print("  ネットワーク接続を確認してください。")
        sys.exit(1)


# ── 送信後のステータス更新 ────────────────────────────
def update_statuses(posts: list[dict], source_file: str, sent_ids: set):
    """送信成功した投稿の status と sent_at を更新してファイルに書き戻す"""
    sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if source_file == str(CSV_FILE):
        _update_csv(sent_ids, sent_at)
    else:
        _update_json(sent_ids, sent_at)


def _update_csv(sent_ids: set, sent_at: str):
    rows = []
    fieldnames = []
    try:
        with open(CSV_FILE, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            for row in reader:
                if str(row.get("id", "")) in sent_ids:
                    row["status"] = SENT_STATUS
                    row["sent_at"] = sent_at
                rows.append(row)
    except csv.Error as e:
        print(f"警告: CSV 読み込みに失敗しました（ステータス未更新）: {e}")
        return

    try:
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except OSError as e:
        print(f"警告: CSV 書き込みに失敗しました（ステータス未更新）: {e}")


def _update_json(sent_ids: set, sent_at: str):
    try:
        with open(JSON_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"警告: JSON 読み込みに失敗しました（ステータス未更新）: {e}")
        return

    posts_list = data["posts"] if isinstance(data, dict) else data
    for post in posts_list:
        if str(post.get("id", "")) in sent_ids:
            post["status"] = SENT_STATUS
            post["sent_at"] = sent_at

    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"警告: JSON 書き込みに失敗しました（ステータス未更新）: {e}")


# ── メインフロー ──────────────────────────────────────
def main():
    print("━" * 50)
    print("  SNS投稿案 Gmail 送信ツール")
    print("━" * 50)

    # 1. 環境変数の読み込み
    gmail_user, app_password, to_email = load_env()
    print(f"送信元: {gmail_user}")
    print(f"送信先: {to_email}")

    # 2. 投稿データの読み込み
    all_posts, source_file = load_posts()
    print(f"データソース: {source_file}（{len(all_posts)} 件読み込み）")

    # 3. 送信対象の抽出
    target_posts = filter_posts(all_posts)
    if not target_posts:
        print("\n送信対象の投稿がありません。")
        print("  条件: status=draft かつ body が空でない かつ risk_check に「安全」または「問題なし」を含む")
        sys.exit(0)

    print(f"送信対象: {len(target_posts)} 件")
    for post in target_posts:
        print(f"  - [{post.get('id')}] {post.get('title', '(タイトルなし)')}")

    # 4. メール本文の作成
    body = build_email_body(target_posts)

    # 5. Gmail 送信
    print("\nGmail に送信中...")
    send_gmail(gmail_user, app_password, to_email, body)
    print("送信完了！")

    # 6. ステータス更新
    sent_ids = {str(p.get("id", "")) for p in target_posts}
    update_statuses(target_posts, source_file, sent_ids)
    print(f"ステータスを「{SENT_STATUS}」に更新しました。")

    print("\n" + "━" * 50)
    print(f"  完了: {len(target_posts)} 件を {to_email} に送信しました")
    print("━" * 50)


if __name__ == "__main__":
    main()
