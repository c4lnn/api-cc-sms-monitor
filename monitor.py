import json
import time
import sys
import signal
import logging
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

TZ_UTC8 = timezone(timedelta(hours=8))

class UTC8Formatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=TZ_UTC8)
        return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S")

handler = logging.StreamHandler()
handler.setFormatter(UTC8Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
logger = logging.getLogger("monitor")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

BASE_URL = "https://api.cc"

def load_config():
    with open("cfg.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if not cfg.get("token"):
        logger.error("❌ 错误: cfg.json 中 token 为空")
        sys.exit(1)
    return cfg

def api_get(path, token):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Authorization": token, "Content-Type": "application/json"},
        method="GET"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def api_post(path, token, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Authorization": token, "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def send_bark(cfg, title, body):
    bark_key = cfg.get("bark_key", "")
    bark_api = cfg.get("bark_api", "https://api.day.app").rstrip("/")
    if not bark_key:
        return
    title_encoded = urllib.parse.quote(title)
    body_encoded = urllib.parse.quote(body)
    url = f"{bark_api}/{bark_key}/{title_encoded}/{body_encoded}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("code") == 200:
                logger.info("📲 Bark 推送成功")
            else:
                logger.warning("📲 Bark 推送失败: %s", result)
    except Exception as e:
        logger.warning("📲 Bark 推送异常: %s", e)

def confirm_categories(cfg):
    result = api_get("/api/v1/app/cate", cfg["token"])
    if result.get("code") != 1:
        logger.error("❌ 获取分类失败: %s", result.get('msg'))
        return
    categories = result["data"]["list"]
    logger.info("📋 项目分类:")
    for cat in categories:
        marker = " ← 当前选择" if cat["id"] == cfg["cate_id"] else ""
        logger.info("   ID=%d  %s%s", cat['id'], cat['name'], marker)

def check_project(cfg):
    try:
        result = api_post("/api/v1/app/list", cfg["token"], {
            "cate_id": cfg["cate_id"],
            "type": cfg["type"],
            "name": cfg["project_name"],
        })
    except urllib.error.HTTPError as e:
        if e.code == 429:
            logger.warning("⏳ 请求过于频繁，等待后重试...")
            time.sleep(30)
            return None
        logger.error("❌ HTTP 错误: %d", e.code)
        return None
    except Exception as e:
        logger.error("❌ 请求失败: %s", e)
        return None

    if result.get("code") != 1:
        logger.error("❌ API 错误: %s", result.get('msg'))
        return None

    items = result.get("data", {}).get("list", [])
    if not items:
        logger.error("❌ 未找到匹配 \"%s\" 的项目", cfg['project_name'])
        return None

    stock = None
    for item in items:
        name = item.get("name", "未知")
        num = int(item.get("num", 0))
        price = float(item.get("price", 0))
        logger.info("%s | 剩余: %d | 价格: ¥%.2f", name, num, price)
        if stock is None:
            stock = num

    return stock

def main():
    cfg = load_config()

    def handle_exit(sig, frame):
        logger.info("👋 已停止监控")
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_exit)

    logger.info("=" * 50)
    logger.info("  API.CC 号码监控")
    logger.info("=" * 50)
    confirm_categories(cfg)

    logger.info("🔍 监控目标: %s (分类ID=%d, 类型=%d)", cfg['project_name'], cfg['cate_id'], cfg['type'])
    logger.info("⏱️  轮询间隔: %d 秒", cfg['interval'])
    logger.info("-" * 50)

    last_stock = -1

    while True:
        stock = check_project(cfg)
        if stock is not None and stock > 0 and last_stock == 0:
            logger.warning("\a" + "=" * 50)
            logger.warning("  !!! 有货了 !!! 快去抢 !!!")
            logger.warning("=" * 50)
            send_bark(cfg, "ChatGPT 有货了!", f"剩余 {stock} 个号码, 快去抢!")
        if stock is not None:
            last_stock = stock
        time.sleep(cfg["interval"])

if __name__ == "__main__":
    main()
