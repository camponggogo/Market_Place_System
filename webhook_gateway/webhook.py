"""
VMS Webhook Gateway - บันทึกลง Database และเลือกบันทึกลงไฟล์ data/{YYYY-MM-DD}/*.json
รับ/ส่ง auth กับ API ธนาคาร: ตรวจสอบลายเซ็น X-Signature หรือ X-Webhook-Signature (HMAC-SHA256)
"""
from flask import Flask, request, jsonify
import os
import json
import hmac
import hashlib
from datetime import datetime

app = Flask(__name__)

# --- Config (config.ini หรือ env) ---
def load_config():
    import configparser
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, "config.ini")
    cfg = configparser.ConfigParser()
    if os.path.exists(config_file):
        cfg.read(config_file, encoding="utf-8")
    # Database
    db_host = os.environ.get("DB_HOST", cfg.get("DATABASE", "DB_HOST", fallback="localhost"))
    db_port = os.environ.get("DB_PORT", cfg.get("DATABASE", "DB_PORT", fallback="3306"))
    db_name = os.environ.get("DB_NAME", cfg.get("DATABASE", "DB_NAME", fallback="market_place_system"))
    db_user = os.environ.get("DB_USER", cfg.get("DATABASE", "DB_USER", fallback="root"))
    db_pass = os.environ.get("DB_PASSWORD", cfg.get("DATABASE", "DB_PASSWORD", fallback="123456") if cfg.has_section("DATABASE") else "123456")
    # Webhook file save
    save_to_files = os.environ.get("WEBHOOK_SAVE_TO_FILES", "").lower() in ("true", "1", "yes")
    if not save_to_files and cfg.has_section("WEBHOOK"):
        save_to_files = cfg.get("WEBHOOK", "SAVE_TO_FILES", fallback="false").lower() in ("true", "1", "yes")
    data_dir = os.environ.get("WEBHOOK_DATA_DIR", cfg.get("WEBHOOK", "DATA_DIR", fallback="data") if cfg.has_section("WEBHOOK") else "data")
    data_dir = os.path.join(base_dir, data_dir) if not os.path.isabs(data_dir) else data_dir
    webhook_secret = os.environ.get("WEBHOOK_SECRET", cfg.get("WEBHOOK", "WEBHOOK_SECRET", fallback="") if cfg.has_section("WEBHOOK") else "").strip()
    return {
        "db_host": db_host,
        "db_port": int(db_port),
        "db_name": db_name,
        "db_user": db_user,
        "db_password": db_pass,
        "save_to_files": save_to_files,
        "data_dir": data_dir,
        "webhook_secret": webhook_secret,
    }

CONFIG = load_config()


def verify_webhook_signature(raw_body):
    """
    ตรวจสอบ X-Signature หรือ X-Webhook-Signature จากธนาคาร (HMAC-SHA256 of raw body).
    raw_body = request.get_data(as_text=False) (เรียกก่อน get_json)
    ถ้า config WEBHOOK_SECRET ว่าง = ไม่ตรวจ (ผ่านเสมอ)
    """
    secret = CONFIG.get("webhook_secret")
    if not secret:
        return True
    if raw_body is None:
        raw_body = b""
    sig_header = request.headers.get("X-Signature") or request.headers.get("X-Webhook-Signature") or request.headers.get("X-Hub-Signature-256")
    if not sig_header:
        return False
    if "=" in sig_header:
        _, expected_hex = sig_header.split("=", 1)
    else:
        expected_hex = sig_header.strip()
    computed = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, expected_hex)


def get_db_connection():
    """เชื่อม MySQL (ใช้ PyMySQL)"""
    try:
        import pymysql
        return pymysql.connect(
            host=CONFIG["db_host"],
            port=CONFIG["db_port"],
            user=CONFIG["db_user"],
            password=CONFIG["db_password"],
            database=CONFIG["db_name"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        app.logger.warning("DB connection failed: %s", e)
        return None


def ensure_webhook_log_table(conn):
    """สร้างตาราง webhook_logs ถ้ายังไม่มี"""
    sql = """
    CREATE TABLE IF NOT EXISTS webhook_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        source VARCHAR(64) NOT NULL,
        payload JSON NOT NULL,
        received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        INDEX idx_source (source),
        INDEX idx_received_at (received_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def save_to_db(source, content):
    """บันทึก payload ลงตาราง webhook_logs"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    try:
        ensure_webhook_log_table(conn)
        payload_json = json.dumps(content, ensure_ascii=False) if content is not None else "{}"
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO webhook_logs (source, payload, received_at) VALUES (%s, %s, NOW(6))",
                (source, payload_json),
            )
        conn.commit()
        return True, cur.lastrowid
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def save_to_file(folder_name, content):
    """บันทึก payload ลงไฟล์ที่ data/{YYYY-MM-DD}/{folder_name}/*.json (เมื่อเปิดใน config)"""
    if not CONFIG["save_to_files"]:
        return True, None
    if content is None:
        return False, "Invalid JSON"
    today = datetime.now().strftime("%Y-%m-%d")
    save_path = os.path.join(CONFIG["data_dir"], today, folder_name)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    filename = datetime.now().strftime("%H-%M-%S-%f") + ".json"
    file_full_path = os.path.join(save_path, filename)
    with open(file_full_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    return True, filename


def handle_webhook(folder_name, content):
    """บันทึก DB ก่อน แล้วถ้าเปิด SAVE_TO_FILES ค่อยบันทึกไฟล์"""
    ok_db, result_db = save_to_db(folder_name, content)
    ok_file, result_file = save_to_file(folder_name, content)
    if not ok_db:
        return False, result_db
    return True, {"db_id": result_db, "file": result_file}


# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def root():
    return jsonify({
        "status": "online",
        "message": "VMS Webhook Gateway is running",
        "endpoints": ["/status", "/paysuccess", "/well2pay"],
        "save_to_files": CONFIG["save_to_files"],
        "data_dir": CONFIG["data_dir"],
        "signature_required": bool(CONFIG.get("webhook_secret")),
    }), 200


def _parse_json_body(raw_body):
    if not raw_body:
        return None
    try:
        return json.loads(raw_body.decode("utf-8"))
    except Exception:
        return None


@app.route("/status", methods=["POST"])
def status_change():
    raw = request.get_data(as_text=False)
    if not verify_webhook_signature(raw):
        return jsonify({"status": "error", "message": "Invalid or missing signature"}), 401
    content = _parse_json_body(raw)
    success, result = handle_webhook("status_change", content)
    if success:
        return jsonify({"status": "success", "type": "callback", "db_id": result.get("db_id"), "file": result.get("file")}), 200
    return jsonify({"status": "error", "message": result}), 400


@app.route("/paysuccess", methods=["POST"])
def paysuccess():
    raw = request.get_data(as_text=False)
    if not verify_webhook_signature(raw):
        return jsonify({"status": "error", "message": "Invalid or missing signature"}), 401
    content = _parse_json_body(raw)
    success, result = handle_webhook("paysuccess", content)
    if success:
        return jsonify({"status": "success", "type": "payment_callback", "db_id": result.get("db_id"), "file": result.get("file")}), 200
    return jsonify({"status": "error", "message": result}), 400


@app.route("/well2pay", methods=["POST"])
def well2pay():
    raw = request.get_data(as_text=False)
    if not verify_webhook_signature(raw):
        return jsonify({"status": "error", "message": "Invalid or missing signature"}), 401
    content = _parse_json_body(raw)
    success, result = handle_webhook("well2pay", content)
    if success:
        return jsonify({"status": "success", "type": "payment_callback", "db_id": result.get("db_id"), "file": result.get("file")}), 200
    return jsonify({"status": "error", "message": result}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port)
