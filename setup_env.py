#!/usr/bin/env python3
"""対話形式で .env を自動作成するセットアップスクリプト"""

import getpass
import os
import sys
from pathlib import Path

ENV_FILE = Path(".env")
EXAMPLE_FILE = Path(".env.example")


def main():
    print("━" * 50)
    print("  .env セットアップウィザード")
    print("━" * 50)
    print()

    # 既存の .env があれば上書き確認
    if ENV_FILE.exists():
        answer = input(".env がすでに存在します。上書きしますか？ [y/N]: ").strip().lower()
        if answer != "y":
            print("キャンセルしました。")
            sys.exit(0)
        print()

    print("以下の情報を入力してください。")
    print("（アプリパスワードの取得方法は README.md を参照）")
    print()

    # GMAIL_USER
    while True:
        gmail_user = input("送信元Gmailアドレス: ").strip()
        if "@" in gmail_user and "." in gmail_user:
            break
        print("  ※ 正しいメールアドレスを入力してください。")

    # GMAIL_APP_PASSWORD（入力時に非表示）
    print()
    print("Gmailアプリパスワード（入力内容は画面に表示されません）")
    print("取得場所: Googleアカウント > セキュリティ > 2段階認証 > アプリパスワード")
    while True:
        app_password = getpass.getpass("アプリパスワード（16文字）: ").strip().replace(" ", "")
        if len(app_password) >= 8:
            break
        print("  ※ アプリパスワードを入力してください（8文字以上）。")

    # TO_EMAIL
    print()
    default_answer = input(f"送信先も同じアドレス（{gmail_user}）でよいですか？ [Y/n]: ").strip().lower()
    if default_answer in ("", "y"):
        to_email = gmail_user
    else:
        while True:
            to_email = input("送信先メールアドレス: ").strip()
            if "@" in to_email and "." in to_email:
                break
            print("  ※ 正しいメールアドレスを入力してください。")

    # .env 書き込み
    content = (
        f"GMAIL_USER={gmail_user}\n"
        f"GMAIL_APP_PASSWORD={app_password}\n"
        f"TO_EMAIL={to_email}\n"
    )
    ENV_FILE.write_text(content, encoding="utf-8")

    # パーミッションを600に（所有者のみ読み書き可）
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass

    print()
    print("━" * 50)
    print("  .env を作成しました！")
    print("━" * 50)
    print(f"  送信元 : {gmail_user}")
    print(f"  送信先 : {to_email}")
    print(f"  パスワード : {'*' * len(app_password)}")
    print()
    print("次のコマンドで投稿をGmailに送信できます:")
    print("  python send_to_gmail.py")


if __name__ == "__main__":
    main()
