"""
Menu Image Service – ดาวน์โหลดรูปจาก URL, resize 480x640, บันทึก local + base64
"""
import base64
import io
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx
from PIL import Image

# โฟลเดอร์เก็บรูป local (rel ต่อ code/)
MENU_IMAGES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "menu_images"
TARGET_SIZE = (480, 640)


def _ensure_dir() -> Path:
    MENU_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    return MENU_IMAGES_DIR


def _resize_image(img: Image.Image, size: Tuple[int, int] = TARGET_SIZE) -> Image.Image:
    """Resize รูปให้พอดี size โดยคง aspect ratio แล้ว crop/pad ให้ตรงขนาด"""
    target_w, target_h = size
    w, h = img.size
    if w == target_w and h == target_h:
        return img
    # scale to cover (fill target, may crop)
    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    # crop center
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def download_and_save(
    image_url: str,
    store_id: int,
    menu_id: int,
    format: str = "JPEG",
    quality: int = 85,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    ดาวน์โหลดรูปจาก URL → resize 480x640 → บันทึก local + base64
    Returns: (image_local_path, image_base64, error_message)
    """
    if not image_url or not image_url.strip():
        return None, None, "image_url is required"

    parsed = urlparse(image_url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
        "Referer": origin + "/",
    }
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(image_url, headers=headers)
            resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
    except Exception as e:
        return None, None, str(e)

    img = _resize_image(img)

    buf = io.BytesIO()
    img.save(buf, format=format, quality=quality)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")

    ext = "jpg" if format.upper() == "JPEG" else "png"
    filename = f"{store_id}_{menu_id}.{ext}"
    abs_path = _ensure_dir() / filename

    try:
        with open(abs_path, "wb") as f:
            img.save(f, format=format, quality=quality)
    except Exception as e:
        return None, b64, f"Saved base64 but local save failed: {e}"

    return filename, b64, None


def fetch_url_to_base64(
    image_url: str,
    max_size: Tuple[int, int] = (160, 160),
    format: str = "JPEG",
    quality: int = 80,
) -> Tuple[Optional[str], Optional[str]]:
    """
    ดาวน์โหลดรูปจาก URL → resize เล็ก → คืน base64 (สำหรับ addon รูป)
    Returns: (base64_string, error_message)
    """
    if not image_url or not image_url.strip():
        return None, "image_url is required"

    parsed = urlparse(image_url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "image/*,*/*;q=0.8",
        "Referer": origin + "/",
    }
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(image_url, headers=headers)
            resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
    except Exception as e:
        return None, str(e)

    img = _resize_image(img, max_size)
    buf = io.BytesIO()
    img.save(buf, format=format, quality=quality)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return b64, None
