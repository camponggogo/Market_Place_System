"""
Mini web app สำหรับแสดง QR Code จากชุดทดสอบ `scripts/test_qr_validation.py`
ดึง biller_id, ref1 (store.token) จาก database

รัน:
    python scripts/qr_code_web.py

เปิด:
    http://localhost:8001/qr-code
    http://localhost:8001/qr-code?store_id=1
    http://localhost:8001/test-tag30-amount
    http://localhost:8001/test-tag30-amount?store_id=1
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

# เพิ่ม root directory เข้า Python path
root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.database import SessionLocal  # noqa: E402
from app.models import Store  # noqa: E402
from app.services.promptpay import (  # noqa: E402
    generate_promptpay_qr_image,
    generate_promptpay_credit_transfer_image,
    generate_promptpay_qr_content,
    generate_promptpay_credit_transfer_content,
)


def get_store_from_db(store_id: Optional[int] = None):
    """ดึงร้านจาก DB ถ้ามี store_id ใช้ id นั้น ไม่เช่นนั้นใช้ร้านแรก"""
    db = SessionLocal()
    try:
        if store_id is not None:
            store = db.query(Store).filter(Store.id == store_id).first()
        else:
            store = db.query(Store).order_by(Store.id).first()
        return store
    finally:
        db.close()


app = FastAPI(title="PromptPay QR Debug", version="1.0")


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


@app.get("/test-tag30-amount", response_class=HTMLResponse)
def test_tag30_amount_page(
    store_id: Optional[int] = Query(None, description="รหัสร้านใน DB ไม่ใส่ใช้ร้านแรก"),
):
    """
    หน้าแสดง QR Code จาก test_tag30_amount.py
    ทดสอบ Tag30 ที่มี amount 14.81
    ดึง biller_id, ref1 (store.token) จาก database
    """
    store = get_store_from_db(store_id)
    if store and getattr(store, "biller_id", None) and getattr(store, "token", None):
        biller_id = "".join(c for c in str(store.biller_id) if c.isdigit())[:15].zfill(15)
        ref1 = store.token
    else:
        biller_id = "011556400219809"
        ref1 = "00000000000010000000"
    amount = 14.81
    
    # Generate QR codes
    qr_content_minimal = generate_promptpay_qr_content(
        biller_id=biller_id,
        ref1=ref1,
        amount=amount,
        include_emv_tags=False
    )
    
    qr_content_emv = generate_promptpay_qr_content(
        biller_id=biller_id,
        ref1=ref1,
        amount=amount,
        include_emv_tags=True
    )
    
    qr_content_no_amount = generate_promptpay_qr_content(
        biller_id=biller_id,
        ref1=ref1,
        amount=None,
        include_emv_tags=False
    )
    
    # Generate QR images
    qr_img_minimal = generate_promptpay_qr_image(
        biller_id=biller_id,
        ref1=ref1,
        amount=amount,
        include_emv_tags=False,
        size=300
    )
    
    qr_img_emv = generate_promptpay_qr_image(
        biller_id=biller_id,
        ref1=ref1,
        amount=amount,
        include_emv_tags=True,
        size=300
    )
    
    qr_img_no_amount = generate_promptpay_qr_image(
        biller_id=biller_id,
        ref1=ref1,
        amount=None,
        include_emv_tags=False,
        size=300
    )
    
    store_label = f"Store id={store.id} {store.name}" if store else "Default (no store)"
    html = f"""
<!doctype html>
<html lang="th">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Test Tag30 With Amount 14.81</title>
    <style>
      body {{
        font-family: Arial, sans-serif;
        padding: 16px;
        background: #f7f7f7;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
      }}
      .card {{
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
      }}
      .title {{
        font-weight: 700;
        margin-bottom: 10px;
        color: #333;
      }}
      .status {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 8px;
      }}
      .status.ok {{
        background: #d4edda;
        color: #155724;
      }}
      .status.fail {{
        background: #f8d7da;
        color: #721c24;
      }}
      img {{
        width: 300px;
        height: 300px;
        display: block;
        margin: 0 auto;
        border: 2px solid #ddd;
        border-radius: 8px;
      }}
      pre {{
        white-space: pre-wrap;
        word-break: break-all;
        background: #0b1020;
        color: #d8e1ff;
        padding: 12px;
        border-radius: 10px;
        font-size: 11px;
        margin-top: 12px;
        max-height: 200px;
        overflow-y: auto;
      }}
      .meta {{
        font-size: 12px;
        color: #666;
        margin-top: 10px;
      }}
      .info {{
        background: #e7f3ff;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 16px;
        border-left: 4px solid #007bff;
      }}
    </style>
  </head>
  <body>
    <h2>Test Tag30 With Amount 14.81</h2>
    <div class="info">
      <strong>ข้อมูลทดสอบ:</strong><br>
      ข้อมูลจาก DB: {_html_escape(store_label)}<br>
      Biller ID: {biller_id}<br>
      Ref1: {ref1}<br>
      Amount: {amount} THB
    </div>
    <div class="grid">
      <div class="card">
        <div class="title">
          Tag30 - Minimal (Amount 14.81)
          <span class="status ok">NEW ORDER</span>
        </div>
        <img src="{qr_img_minimal}" alt="Tag30 Minimal QR" />
        <pre>{_html_escape(qr_content_minimal)}</pre>
        <div class="meta">Length: {len(qr_content_minimal)} chars | Order: 53 → 54 → 58</div>
      </div>

      <div class="card">
        <div class="title">Tag30 - EMV (Amount 14.81)</div>
        <img src="{qr_img_emv}" alt="Tag30 EMV QR" />
        <pre>{_html_escape(qr_content_emv)}</pre>
        <div class="meta">Length: {len(qr_content_emv)} chars | Order: 52 → 53 → 54 → 58</div>
      </div>

      <div class="card">
        <div class="title">Tag30 - No Amount (Reference)</div>
        <img src="{qr_img_no_amount}" alt="Tag30 No Amount QR" />
        <pre>{_html_escape(qr_content_no_amount)}</pre>
        <div class="meta">Length: {len(qr_content_no_amount)} chars | Scans OK ✅</div>
      </div>
    </div>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@app.get("/qr-code", response_class=HTMLResponse)
def qr_code_page(
    store_id: Optional[int] = Query(None, description="รหัสร้าน ดึง biller_id, ref1 จาก DB"),
    mobile: str = Query("0909199270"),
    amount: float = Query(101.25),
    biller_id: Optional[str] = Query(None),
    ref1: Optional[str] = Query(None),
    merchant_name: str = Query("NA"),
    merchant_city: str = Query("BANGKOK"),
):
    """
    หน้าแสดง QR สำหรับสแกนทดสอบ
    ถ้าใส่ store_id จะดึง biller_id, ref1 (store.token) จาก database

    ตัวอย่าง:
      http://localhost:8001/qr-code?store_id=1
      http://localhost:8001/qr-code?store_id=1&amount=50
      http://localhost:8001/qr-code?mobile=0909199270&amount=101.25&biller_id=011556400219809&ref1=0000001
    """
    store = get_store_from_db(store_id) if store_id is not None else None
    # ดึงจาก DB ถ้ามี store
    if store:
        if biller_id is None and getattr(store, "biller_id", None):
            biller_id = "".join(c for c in str(store.biller_id) if c.isdigit())[:15].zfill(15)
        if ref1 is None and getattr(store, "token", None):
            ref1 = store.token
    if biller_id is None:
        biller_id = "011556400219809"
    if ref1 is None:
        ref1 = "00000000000010000000"
    mobile_number = mobile

    # Generate payloads
    tag29_payload = generate_promptpay_credit_transfer_content(
        mobile_number=mobile_number,
        amount=amount,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
    )
    tag29_payload_min = generate_promptpay_credit_transfer_content(
        mobile_number=mobile_number,
        amount=amount,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        include_emv_tags=False,
    )
    tag30_payload_simple = generate_promptpay_qr_content(
        biller_id=biller_id,
        ref1=ref1,
        ref2=None,
        ref3=None,
        amount=None,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
    )
    tag30_payload_amount = generate_promptpay_qr_content(
        biller_id=biller_id,
        ref1=ref1,
        ref2=None,
        ref3=None,
        amount=amount,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
    )

    # Generate QR images (base64 data URIs)
    tag29_img = generate_promptpay_credit_transfer_image(
        mobile_number=mobile_number,
        amount=amount,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        size=300,
    )
    tag29_img_min = generate_promptpay_credit_transfer_image(
        mobile_number=mobile_number,
        amount=amount,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        include_emv_tags=False,
        size=300,
    )
    tag30_img_simple = generate_promptpay_qr_image(
        biller_id=biller_id,
        ref1=ref1,
        ref2=None,
        ref3=None,
        amount=None,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        size=300,
    )
    tag30_img_amount = generate_promptpay_qr_image(
        biller_id=biller_id,
        ref1=ref1,
        ref2=None,
        ref3=None,
        amount=amount,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        size=300,
    )

    # Compare with promptpay-qr example from screenshot (mobile=000-000-0000, amount=4.22)
    expected_promptpay_qr_payload = (
        "00020101021229370016A000000677010111011300660000000005802TH530376"
        "544044.226304E469"
    )
    sample_match = (
        mobile_number.replace("-", "").strip() == "0000000000"
        and abs(amount - 4.22) < 1e-9
        and tag29_payload_min == expected_promptpay_qr_payload
    )

    source_note = ""
    if store_id is not None:
        source_note = f" | ข้อมูลร้านจาก DB: id={store_id}" + (f" ({store.name})" if store else " (ไม่พบร้าน)")

    html = f"""
<!doctype html>
<html lang="th">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PromptPay QR Debug</title>
    <style>
      body {{
        font-family: Arial, sans-serif;
        padding: 16px;
        background: #f7f7f7;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
      }}
      .card {{
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
      }}
      .title {{
        font-weight: 700;
        margin-bottom: 10px;
      }}
      img {{
        width: 300px;
        height: 300px;
        display: block;
        margin: 0 auto;
      }}
      pre {{
        white-space: pre-wrap;
        word-break: break-all;
        background: #0b1020;
        color: #d8e1ff;
        padding: 12px;
        border-radius: 10px;
        font-size: 12px;
        margin-top: 12px;
      }}
      .meta {{
        font-size: 12px;
        color: #666;
        margin-top: 10px;
      }}
    </style>
  </head>
  <body>
    <h2>PromptPay QR Debug</h2>
    <div class="meta">
      เปิดหน้านี้เพื่อสแกนทดสอบ (พอร์ต 8001).{_html_escape(source_note)}<br>
      ค่าที่ใช้:
      <code>mobile={_html_escape(mobile_number)}</code>,
      <code>amount={amount}</code>,
      <code>biller_id={_html_escape(biller_id)}</code>,
      <code>ref1={_html_escape(ref1)}</code>,
      <code>merchant_name={_html_escape(merchant_name)}</code>,
      <code>merchant_city={_html_escape(merchant_city)}</code>
    </div>
    <div class="grid">
      <div class="card">
        <div class="title">Tag29 - Credit Transfer (EMV tags)</div>
        <img src="{tag29_img}" alt="Tag29 QR" />
        <pre>{_html_escape(tag29_payload)}</pre>
        <div class="meta">Length: {len(tag29_payload)} chars</div>
      </div>

      <div class="card">
        <div class="title">Tag29 - Minimal (match promptpay-qr)</div>
        <img src="{tag29_img_min}" alt="Tag29 Minimal QR" />
        <pre>{_html_escape(tag29_payload_min)}</pre>
        <div class="meta">Length: {len(tag29_payload_min)} chars</div>
        <div class="meta">
          promptpay-qr sample match (mobile=0000000000, amount=4.22): {"✅" if sample_match else "❌"}
        </div>
        <div class="meta">
          Expected sample payload:<br/>
          <code>{_html_escape(expected_promptpay_qr_payload)}</code>
        </div>
      </div>

      <div class="card">
        <div class="title">Tag30 - Simple (Biller + Ref1, no amount)</div>
        <img src="{tag30_img_simple}" alt="Tag30 Simple QR" />
        <pre>{_html_escape(tag30_payload_simple)}</pre>
        <div class="meta">Length: {len(tag30_payload_simple)} chars</div>
      </div>

      <div class="card">
        <div class="title">Tag30 - With Amount ({amount})</div>
        <img src="{tag30_img_amount}" alt="Tag30 Amount QR" />
        <pre>{_html_escape(tag30_payload_amount)}</pre>
        <div class="meta">Length: {len(tag30_payload_amount)} chars</div>
      </div>
    </div>
  </body>
</html>
"""
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")


