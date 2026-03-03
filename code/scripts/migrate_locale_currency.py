"""
Migration: สร้างตาราง locales, currencies, app_settings, translations
และใส่ข้อมูลตัวอย่าง (ภาษา, หน่วยเงิน, คำแปล)
รันครั้งเดียว: python scripts/migrate_locale_currency.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine
from app.models import Base, Locale, Currency, AppSetting, Translation


# ข้อมูลตัวอย่าง: ภาษา
LOCALES = [
    ("th", "ไทย"),
    ("en", "English"),
    ("lo", "ລາວ"),
    ("my", "မြန်မာ"),
    ("kh", "ខ្មែរ"),
    ("ms", "Melayu"),
    ("shn", "တႆး"),
    ("zh", "中文"),
    ("ru", "Русский"),
]

# ข้อมูลตัวอย่าง: หน่วยเงิน
CURRENCIES = [
    ("THB", "฿", "Baht"),
    ("USD", "$", "Dollar"),
    ("LAK", "₭", "Kip"),
    ("MMK", "K", "Kyat"),
    ("KHR", "៛", "Riel"),
    ("MYR", "RM", "Ringgit"),
    ("CNY", "¥", "Yuan"),
    ("RUB", "₽", "Ruble"),
]

# คำแปลตัวอย่าง (key -> th, en, lo, my, kh, ms, shn, zh, ru)
TRANSLATIONS = {
    "store_pos": {"th": "Store POS", "en": "Store POS", "lo": "Store POS", "my": "Store POS", "kh": "Store POS", "ms": "Store POS", "shn": "Store POS", "zh": "收银台", "ru": "Касса"},
    "products_services": {"th": "รายการสินค้าและบริการ", "en": "Products & Services", "lo": "ສິນຄ້າ ແລະ ບໍລິການ", "my": "ပစ္စည်းများနှင့်ဝန်ဆောင်မှုများ", "kh": "ផលិតផល និងសេវាកម្ម", "ms": "Produk & Perkhidmatan", "shn": "ၵူၼ်းမိုဝ်း", "zh": "商品与服务", "ru": "Товары и услуги"},
    "order_list": {"th": "รายการสั่งซื้อ", "en": "Order List", "lo": "ລາຍການສັ່ງຊື້", "my": "စာရင်းမှာယူမှု", "kh": "បញ្ជីការបញ្ជាទិញ", "ms": "Senarai Pesanan", "shn": "တၢင်းၶၢမ်ႇ", "zh": "订单列表", "ru": "Список заказов"},
    "total": {"th": "รวม", "en": "Total", "lo": "ລວມ", "my": "စုစုပေါင်း", "kh": "សរុប", "ms": "Jumlah", "shn": "ၵမ်းလိၼ်း", "zh": "合计", "ru": "Итого"},
    "no_items": {"th": "ยังไม่มีรายการ", "en": "No items yet", "lo": "ຍັງບໍ່ມີລາຍການ", "my": "မရှိသေးပါ", "kh": "មិនមានធាតុនៅឡើយ", "ms": "Tiada item lagi", "shn": "မႂ်ႈမီးတၢင်း", "zh": "暂无项目", "ru": "Пока пусто"},
    "barcode_placeholder": {"th": "พิมพ์หรือสแกนบาร์โค้ด", "en": "Type or scan barcode", "lo": "ພິມ ຫຼື ສະແກນບາດໂຄດ", "my": "ရိုက်သွင်းသို့မဟုတ်စကင်န်", "kh": "វាយ ឬស្កេនបាកូដ", "ms": "Taip atau imbasan kod bar", "shn": "တူၵ်းလဵၵ်း", "zh": "输入或扫描条形码", "ru": "Введите или отсканируйте штрихкод"},
    "add_to_order": {"th": "เพิ่มลงรายการ", "en": "Add to Order", "lo": "ເພີ່ມເຂົ້າລາຍການ", "my": "စာရင်းသို့ထည့်ပါ", "kh": "បន្ថែមទៅការបញ្ជាទិញ", "ms": "Tambah ke Pesanan", "shn": "ထတ်းပၼ်", "zh": "加入订单", "ru": "Добавить в заказ"},
    "cancel": {"th": "ยกเลิก", "en": "Cancel", "lo": "ຍົກເລີກ", "my": "ပယ်ဖျက်", "kh": "បោះបង់", "ms": "Batal", "shn": "ယွၼ်း", "zh": "取消", "ru": "Отмена"},
    "clear_items": {"th": "ล้างรายการ", "en": "Clear Items", "lo": "ລ້າງລາຍການ", "my": "ရှင်းလင်းပစ္စည်းများ", "kh": "សម្អាតធាតុ", "ms": "Kosongkan Item", "shn": "လီၵဝ်း", "zh": "清空", "ru": "Очистить"},
    "settings": {"th": "ตั้งค่า", "en": "Settings", "lo": "ການຕັ້ງຄ່າ", "my": "ဆက်တင်များ", "kh": "ការកំណត់", "ms": "Tetapan", "shn": "တၢင်းၶၢမ်ႇ", "zh": "设置", "ru": "Настройки"},
    "manage_menu": {"th": "จัดการเมนู", "en": "Manage Menu", "lo": "ຈັດການເມນູ", "my": "မီနူးစီမံခန့်ခွဲမှု", "kh": "គ្រប់គ្រងម៉ឺនុយ", "ms": "Urus Menu", "shn": "ၶၢမ်ႇ", "zh": "管理菜单", "ru": "Управление меню"},
    "select_addons": {"th": "เลือกเพิ่มเติม (ถ้ามี)", "en": "Select add-ons (optional)", "lo": "ເລືອກເພີ່ມເຕີມ", "my": "ရွေးချယ်ပါ (ရွေးချယ်နိုင်သည်)", "kh": "ជ្រើសរើសកម្មវិធីបន្ថែម", "ms": "Pilih tambahan (pilihan)", "shn": "လိမ်ႉပၼ်", "zh": "选择附加项（可选）", "ru": "Выберите дополнения"},
    "amount_received": {"th": "จำนวนเงินที่รับ", "en": "Amount received", "lo": "ຈຳນວນເງິນທີ່ຮັບ", "my": "လက်ခံငွေပမာဏ", "kh": "ចំនួនទឹកប្រាក់ដែលទទួល", "ms": "Jumlah diterima", "shn": "ၶၢမ်ႇ", "zh": "实收金额", "ru": "Полученная сумма"},
    "change": {"th": "เงินทอน", "en": "Change", "lo": "ເງິນທອນ", "my": "ပြန်အမ်း", "kh": "ទឹកប្រាក់អាប់", "ms": "Baki", "shn": "ၶၢမ်ႇ", "zh": "找零", "ru": "Сдача"},
    "pay_cash": {"th": "รับเงินแล้ว และดำเนินการต่อ", "en": "Received and proceed", "lo": "ຮັບເງິນແລ້ວ ແລະ ດຳເນີນການຕໍ່", "my": "လက်ခံပြီးဆက်လုပ်ပါ", "kh": "ទទួលហើយបន្ត", "ms": "Diterima dan teruskan", "shn": "လႆႈယူငၢမ်း", "zh": "已收款，继续", "ru": "Получено, продолжить"},
    "promptpay": {"th": "PromptPay", "en": "PromptPay", "lo": "PromptPay", "my": "PromptPay", "kh": "PromptPay", "ms": "PromptPay", "shn": "PromptPay", "zh": "PromptPay", "ru": "PromptPay"},
    "credit_debit": {"th": "Credit/Debit", "en": "Credit/Debit", "lo": "Credit/Debit", "my": "Credit/Debit", "kh": "Credit/Debit", "ms": "Credit/Debit", "shn": "Credit/Debit", "zh": "信用卡/借记卡", "ru": "Кредит/Дебет"},
    "cash": {"th": "เงินสด", "en": "Cash", "lo": "ເງິນສົດ", "my": "ငွေသား", "kh": "ទឹកប្រាក់សាច់", "ms": "Tunai", "shn": "ၶၢမ်ႇ", "zh": "现金", "ru": "Наличные"},
    "print_order_qr": {"th": "พิมพ์ Order + QR", "en": "Print Order + QR", "lo": "ພິມ Order + QR", "my": "ပရင့်အမိန့် + QR", "kh": "បោះពុម្ភ Order + QR", "ms": "Cetak Pesanan + QR", "shn": "ပရင့် Order + QR", "zh": "打印订单+二维码", "ru": "Печать заказа + QR"},
    "print_receipt": {"th": "พิมพ์ใบรับเงิน (หลังได้รับเงิน)", "en": "Print Receipt (after payment)", "lo": "ພິມໃບຮັບເງິນ", "my": "ပရင့်လက်ခံငွေပမာဏ", "kh": "បោះពុម្ភបង្កាន់ដៃ", "ms": "Cetak Resit (selepas bayaran)", "shn": "ပရင့်ၶၢမ်ႇ", "zh": "打印收据（收款后）", "ru": "Печать чека (после оплаты)"},
    "deduct_amount": {"th": "หักยอดเงิน", "en": "Deduct amount", "lo": "ຫັກຍອດເງິນ", "my": "ငွေပမာဏဖယ်ရှား", "kh": "ដកចំនួន", "ms": "Tolak jumlah", "shn": "ၶၢမ်ႇ", "zh": "扣款", "ru": "Списать сумму"},
    "foodcourt_id_placeholder": {"th": "สแกนหรือกรอก Food Court ID (หักยอด)", "en": "Scan or enter Food Court ID", "lo": "ສະແກນ ຫຼື ປ້ອນ Food Court ID", "my": "စကင်န်သို့မဟုတ်ထည့်သွင်း Food Court ID", "kh": "ស្កេន ឬបញ្ចូល Food Court ID", "ms": "Imbas atau masukkan Food Court ID", "shn": "တူၵ်းလဵၵ်း Food Court ID", "zh": "扫描或输入美食广场ID", "ru": "Сканируйте или введите ID фудкорта"},
    "back_to_pos": {"th": "กลับไป Store POS", "en": "Back to Store POS", "lo": "ກັບໄປ Store POS", "my": "ပြန်သွား Store POS", "kh": "ត្រឡប់ទៅ Store POS", "ms": "Kembali ke Store POS", "shn": "ၵူၼ်းမိုဝ်း", "zh": "返回收银台", "ru": "Назад в кассу"},
    "settings_title": {"th": "ตั้งค่า Store POS", "en": "Store POS Settings", "lo": "ການຕັ້ງຄ່າ Store POS", "my": "Store POS ဆက်တင်များ", "kh": "ការកំណត់ Store POS", "ms": "Tetapan Store POS", "shn": "တၢင်းၶၢမ်ႇ", "zh": "收银台设置", "ru": "Настройки кассы"},
    "language": {"th": "ภาษา", "en": "Language", "lo": "ພາສາ", "my": "ဘာသာစကား", "kh": "ភាសា", "ms": "Bahasa", "shn": "ၵႂၢမ်း", "zh": "语言", "ru": "Язык"},
    "currency": {"th": "หน่วยเงิน", "en": "Currency", "lo": "ເງິນ", "my": "ငွေကြေး", "kh": "រូបិយប័ណ្ណ", "ms": "Mata wang", "shn": "ၶၢမ်ႇ", "zh": "货币", "ru": "Валюта"},
    "save_settings": {"th": "บันทึกการตั้งค่า", "en": "Save Settings", "lo": "ບັນທຶກການຕັ້ງຄ່າ", "my": "ဆက်တင်များသိမ်းပါ", "kh": "រក្សាទុកការកំណត់", "ms": "Simpan Tetapan", "shn": "ထတ်းပၼ်", "zh": "保存设置", "ru": "Сохранить настройки"},
    "manage_menu_title": {"th": "จัดการเมนู", "en": "Manage Menu", "lo": "ຈັດການເມນູ", "my": "မီနူးစီမံခန့်ခွဲမှု", "kh": "គ្រប់គ្រងម៉ឺនុយ", "ms": "Urus Menu", "shn": "ၶၢမ်ႇ", "zh": "管理菜单", "ru": "Управление меню"},
    "menu_list": {"th": "รายการเมนู", "en": "Menu List", "lo": "ລາຍການເມນູ", "my": "မီနူးစာရင်း", "kh": "បញ្ជីម៉ឺនុយ", "ms": "Senarai Menu", "shn": "တၢင်းၶၢမ်ႇ", "zh": "菜单列表", "ru": "Список меню"},
    "save": {"th": "บันทึก", "en": "Save", "lo": "ບັນທຶກ", "my": "သိမ်းပါ", "kh": "រក្សាទុក", "ms": "Simpan", "shn": "ထတ်းပၼ်", "zh": "保存", "ru": "Сохранить"},
    "edit_addon": {"th": "แก้ไข Add-on", "en": "Edit Add-on", "lo": "ແກ້ໄຂ Add-on", "my": "Add-on ပြင်ပါ", "kh": "កែសម្រួល Add-on", "ms": "Edit Add-on", "shn": "ၶၢမ်ႇ", "zh": "编辑附加项", "ru": "Редактировать дополнения"},
    "image": {"th": "รูป", "en": "Image", "lo": "ຮູບ", "my": "ပုံ", "kh": "រូបភាព", "ms": "Imej", "shn": "ပုၼ်ႇ", "zh": "图片", "ru": "Изображение"},
    "no_menu": {"th": "ยังไม่มีเมนู", "en": "No menu yet", "lo": "ຍັງບໍ່ມີເມນູ", "my": "မီနူးမရှိသေးပါ", "kh": "មិនមានម៉ឺនុយនៅឡើយ", "ms": "Tiada menu lagi", "shn": "မႂ်ႈမီးတၢင်း", "zh": "暂无菜单", "ru": "Меню пока нет"},
    "add_addon": {"th": "เพิ่มเมนูพิเศษ", "en": "Add add-on", "lo": "ເພີ່ມເມນູເພີ່ມເຕີມ", "my": "Add-on ထည့်ပါ", "kh": "បន្ថែម Add-on", "ms": "Tambah add-on", "shn": "ထတ်းပၼ်", "zh": "添加附加项", "ru": "Добавить дополнение"},
    "remove": {"th": "ลบ", "en": "Remove", "lo": "ລຶບ", "my": "ဖယ်ရှားပါ", "kh": "ដកចេញ", "ms": "Buang", "shn": "ယွၼ်း", "zh": "删除", "ru": "Удалить"},
}


def migrate():
    # สร้างตาราง
    Base.metadata.create_all(bind=engine, tables=[Locale.__table__, Currency.__table__, AppSetting.__table__, Translation.__table__])

    from sqlalchemy.orm import Session
    db = Session(bind=engine)

    try:
        # Seed locales
        if db.query(Locale).count() == 0:
            for code, name in LOCALES:
                db.add(Locale(code=code, name=name))
            db.commit()
            print("Migration: Seeded locales")

        # Seed currencies
        if db.query(Currency).count() == 0:
            for code, symbol, name in CURRENCIES:
                db.add(Currency(code=code, symbol=symbol, name=name))
            db.commit()
            print("Migration: Seeded currencies")

        # Seed app_settings (default: ไทย, บาท)
        if db.query(AppSetting).filter(AppSetting.key == "locale").first() is None:
            db.add(AppSetting(key="locale", value="th"))
            db.add(AppSetting(key="currency_code", value="THB"))
            db.add(AppSetting(key="currency_symbol", value="฿"))
            db.add(AppSetting(key="currency_name", value="Baht"))
            db.commit()
            print("Migration: Seeded app_settings")

        # Seed translations (เพิ่ม key ใหม่ถ้ายังไม่มี)
        existing_keys = set()
        for r in db.query(Translation.locale, Translation.key).distinct():
            existing_keys.add((r.locale, r.key))
        added = 0
        for key, vals in TRANSLATIONS.items():
            for locale, value in vals.items():
                if (locale, key) not in existing_keys:
                    db.add(Translation(locale=locale, key=key, value=value))
                    existing_keys.add((locale, key))
                    added += 1
        if added > 0:
            db.commit()
            print("Migration: Added", added, "translations")
        elif db.query(Translation).count() == 0:
            for key, vals in TRANSLATIONS.items():
                for locale, value in vals.items():
                    db.add(Translation(locale=locale, key=key, value=value))
            db.commit()
            print("Migration: Seeded translations")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
    print("Migration: locale/currency done")
