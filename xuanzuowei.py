import time
import requests
from datetime import datetime, timedelta, timezone

url = "https://api.jingjia6.com/zuo/selected"


headers = {
    "Host": "api.jingjia6.com",
	"Connection": "keep-alive",
	"appid": "wxee63c38f3aa6f658",
	"User-Agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
		"AppleWebKit/537.36 (KHTML, like Gecko) "
		"Chrome/132.0.0.0 Safari/537.36 "
		"MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI "
		"MiniProgramEnv/Windows WindowsWechat/WMPF "
		"WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2540621) "
		"XWEB/16203"
	),
	"xweb_xhr": "1",
	"Content-Type": "application/json",
    # 1：可以用yakit抓包获取token
	"token": "your_token",
	"Accept": "*/*",
	"Sec-Fetch-Site": "cross-site",
	"Sec-Fetch-Mode": "cors",
	"Sec-Fetch-Dest": "empty",
	"Referer": "https://servicewechat.com/wxee63c38f3aa6f658/83/page-frame.html",
	# 不设置 Content-Length（由库自动计算）；不强制 Accept-Encoding 以简化解压
	"Accept-Language": "zh-CN,zh;q=0.9",
}
# 2：选座位要填的用户名
USER_NAME = "your_user_name"
# 3：选座位开始时间
start_time_str = "2025-01-01 00:00:01.850"
# 4：可以用yakit抓包获取要选座位的id
USER_ID = "your_user_id"
# 5：选座位的目标座位
seat_list = ["1_1"]

beijing_tz = timezone(timedelta(hours=8))

# 兼容有无毫秒的小数秒
_dt = None
for _fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
    try:
        _dt = datetime.strptime(start_time_str, _fmt)
        break
    except ValueError:
        _dt = None
if _dt is None:
    raise ValueError("start_time_str 格式不正确，应为 'YYYY-MM-DD HH:MM:SS[.mmm]'")

start_time = _dt.replace(tzinfo=beijing_tz)

print(f"目标开始时间: {start_time}")

# 粗等 + 细等：先按较大步长睡眠，最后 20ms 内改为 1ms 粒度
while True:
    now = datetime.now(beijing_tz)
    if now >= start_time:
        break
    remaining = (start_time - now).total_seconds()
    if remaining > 0.02:
        # 留出 10ms 安全边际，避免过冲
        time.sleep(min(remaining - 0.01, 0.5))
    else:
        time.sleep(0.001)

print("开始抢座！")

for seat in seat_list:
    while True:  # 当前座位循环，直到抢到 or 确认失败
        payload = {
            f"name.{seat}": USER_NAME,
            "id": USER_ID,
            "zuo": [seat]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            data = response.json()
            info = data.get("info", "")
            print(f"尝试座位 {seat}: {info}")

            if "成功选择 1 个座位" in info:
                print(f"✅ 抢座成功！座位号: {seat}")
                exit(0)  # 抢到直接退出整个程序

            elif "请勿频繁" in info:
                print("⚠️ 被限制访问，等待 0.1 秒后重试...")
                time.sleep(0.1)  # 等待再重试（仍然是当前座位）

            else:
                print("❌ 当前座位失败，尝试下一个...")
                time.sleep(2.5)  # 失败后稍等再换下一个
                break  # 跳出 while True，进入下一个座位

        except Exception as e:
            print(f"请求座位 {seat} 出错: {e}")
            time.sleep(1)
            # 继续当前座位重试