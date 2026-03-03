"""
Helper สำหรับ resolve ข้อความหลายภาษา (name_i18n, description_i18n)
"""
import json
from typing import Optional


def resolve_i18n(i18n_json: Optional[str], default: Optional[str], locale: str) -> str:
    """
    คืนค่าตาม locale จาก JSON {"th":"...","en":"..."}
    Fallback: locale -> th -> en -> default
    """
    if not i18n_json or not i18n_json.strip():
        return default or ""
    try:
        data = json.loads(i18n_json)
        if not isinstance(data, dict):
            return default or ""
        for lang in (locale, "th", "en"):
            if lang in data and data[lang]:
                return str(data[lang]).strip()
        return default or (list(data.values())[0] if data else "")
    except (json.JSONDecodeError, TypeError):
        return default or ""


def resolve_addon_options(addon_options_json: Optional[str], locale: str) -> Optional[str]:
    """
    แปลง addon_options ให้ name ตาม locale
    Format: [{"name":"ไข่ดาว","name_i18n":{"en":"Fried Egg"},"price":10},...]
    """
    if not addon_options_json or not addon_options_json.strip():
        return addon_options_json
    try:
        arr = json.loads(addon_options_json)
        if not isinstance(arr, list):
            return addon_options_json
        out = []
        for item in arr:
            if not isinstance(item, dict):
                out.append(item)
                continue
            copy = dict(item)
            name_i18n = copy.get("name_i18n")
            default_name = copy.get("name", "")
            if name_i18n and isinstance(name_i18n, dict):
                resolved = resolve_i18n(json.dumps(name_i18n), default_name, locale)
                copy["name"] = resolved
            out.append(copy)
        return json.dumps(out, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return addon_options_json
