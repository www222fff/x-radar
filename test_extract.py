from extract import extract_codes

sample = """苹果 App Store / Google Play 搜索：Cue

🎁 新用户福利：
8 核 16G 云电脑（以账户页面展示为准）
Plus 一个月免费试用

🎟️ 邀请码：9XAJP、V6CJ5"""

got = sorted(extract_codes(sample))
want = ["9XAJP", "V6CJ5"]
print("extracted:", got, "->", "PASS" if got == want else f"FAIL (want {want})")

noise = extract_codes("HELLO WORLD 12345 ABCDE https://x.com HTTPS 8核16G CLOUD")
print("noise:", noise, "->", "PASS" if noise == [] else "FAIL")

raise SystemExit(0 if got == want and noise == [] else 1)
