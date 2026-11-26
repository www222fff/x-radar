"""Add one X account to the twscrape pool.

Two modes, configured in account.txt (create it yourself, keep it private,
never commit). Mode A is auto-detected when `cookies=` is present.

Mode A - cookies (no login, needs a browser once to copy cookies):
    username=your_handle_without_at
    cookies=auth_token=XXXX; ct0=YYYY

Mode B - credentials (NO browser; twscrape logs in and reads the X
verification code from your mailbox over IMAP):
    username=your_handle_without_at
    password=your_x_password
    email=your_login_email@example.com
    email_password=IMAP_APP_PASSWORD
    # optional, only if the account has 2FA (TOTP) enabled:
    mfa_code=BASE32_TOTP_SECRET
"""
import os
import sys
import asyncio
from twscrape import API

BASE = os.path.dirname(os.path.abspath(__file__))
ACC_FILE = os.path.join(BASE, "account.txt")
DB_PATH = os.path.join(BASE, "accounts.db")


def read_conf():
    conf = {}
    with open(ACC_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            conf[key.strip()] = value.strip()
    return conf


async def test_search(api):
    try:
        n = 0
        async for _ in api.search("hello", limit=1):
            n += 1
        print("凭据可用,搜索测试通过" if n else "已添加,测试搜索暂无结果(可能正常)")
    except Exception as e:
        print("已添加,但测试搜索报错(凭据可能有问题):", e)


async def main():
    if not os.path.exists(ACC_FILE):
        print(f"缺少 {ACC_FILE}(参考 account.example.txt)")
        sys.exit(1)
    conf = read_conf()
    username = conf.get("username")
    if not username:
        print("account.txt 需要 username=")
        sys.exit(1)

    api = API(DB_PATH)

    if conf.get("cookies"):
        await api.pool.add_account_cookies(username, conf["cookies"])
        print("已用 cookie 添加账号:", username)
        await test_search(api)
        return

    password = conf.get("password")
    email = conf.get("email")
    email_password = conf.get("email_password")
    if not (password and email and email_password):
        print("账号密码模式需要 password=、email=、email_password= 三项(或改用 cookies=)")
        sys.exit(1)

    await api.pool.add_account(
        username, password, email, email_password,
        mfa_code=conf.get("mfa_code") or None,
    )
    print("已添加账号(密码模式),开始登录(会去邮箱读验证码)...")
    await api.pool.login_all()
    accs = await api.pool.get_all()
    for a in accs:
        if a.username == username:
            print(f"登录状态: active={a.active}")
    await test_search(api)


if __name__ == "__main__":
    asyncio.run(main())
