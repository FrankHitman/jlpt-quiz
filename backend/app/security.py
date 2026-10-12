"""註冊/登入的安全防護：圖形驗證碼 + 按 IP 限流（防惡意批量註冊/撞庫）。

全部狀態保存在進程內存：重啟後清空，適合本應用的單進程部署。
"""
from __future__ import annotations

import base64
import io
import random
import secrets
import string
import time
from collections import defaultdict, deque

from fastapi import Request

# ---------------------------------------------------------------- 限流

_hits: dict[str, deque[float]] = defaultdict(deque)


def get_client_ip(request: Request) -> str:
    """取客戶端 IP：反向代理場景取 X-Forwarded-For 首個，否則直連 IP。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """滑動窗口限流：超限返回 False。key 形如 f"register:{ip}"。"""
    now = time.time()
    dq = _hits[key]
    while dq and dq[0] <= now - window_seconds:
        dq.popleft()
    if len(dq) >= limit:
        return False
    dq.append(now)
    # 防止內存無限增長：定期清理空隊列
    if len(_hits) > 10000:
        for k in [k for k, v in _hits.items() if not v]:
            del _hits[k]
    return True


# ---------------------------------------------------------------- 圖形驗證碼

_CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 去掉易混淆的 0/O/1/I
_captchas: dict[str, tuple[str, float]] = {}  # captcha_id -> (code, expires_at)
CAPTCHA_TTL = 300  # 5 分鐘


def _draw_captcha_image(code: str) -> str:
    """生成驗證碼 PNG，返回 data URL（base64）。"""
    from PIL import Image, ImageDraw, ImageFont

    w, h = 150, 52
    img = Image.new("RGB", (w, h), (245, 243, 238))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
    except OSError:
        font = ImageFont.load_default(size=34)

    # 隨機背景干擾線
    for _ in range(4):
        x1, y1 = random.randint(0, w), random.randint(0, h)
        x2, y2 = random.randint(0, w), random.randint(0, h)
        draw.line(
            [(x1, y1), (x2, y2)],
            fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)),
            width=1,
        )
    # 逐字繪製（隨機位置/傾斜/顏色）
    x = 12
    for ch in code:
        y = random.randint(4, 14)
        color = (
            random.randint(20, 90),
            random.randint(20, 90),
            random.randint(120, 200),
        )
        # 單字小圖旋轉後貼回，製造傾斜
        glyph = Image.new("RGBA", (34, 40), (0, 0, 0, 0))
        ImageDraw.Draw(glyph).text((2, 2), ch, font=font, fill=color + (255,))
        glyph = glyph.rotate(random.randint(-18, 18), expand=True, resample=Image.BICUBIC)
        img.paste(glyph, (x, y), glyph)
        x += 26
    # 噪點
    for _ in range(120):
        draw.point(
            (random.randint(0, w - 1), random.randint(0, h - 1)),
            fill=(random.randint(120, 200),) * 3,
        )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def new_captcha() -> tuple[str, str]:
    """返回 (captcha_id, image_data_url)。"""
    now = time.time()
    # 清理過期
    for cid in [c for c, (_, exp) in _captchas.items() if exp < now]:
        del _captchas[cid]
    code = "".join(secrets.choice(_CAPTCHA_CHARS) for _ in range(5))
    cid = secrets.token_urlsafe(16)
    _captchas[cid] = (code, now + CAPTCHA_TTL)
    return cid, _draw_captcha_image(code)


def verify_captcha(captcha_id: str, code: str) -> bool:
    """校驗驗證碼：一次性使用（無論對錯都銷毀），忽略大小寫。"""
    entry = _captchas.pop(captcha_id, None)
    if entry is None:
        return False
    expected, exp = entry
    if time.time() > exp:
        return False
    return expected == code.strip().upper()
