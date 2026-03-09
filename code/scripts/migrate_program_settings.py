"""
Migration: สร้างตาราง program_settings สำหรับเก็บ labels หลายภาษา
แต่ละ row = label key, แต่ละ column = ภาษา (label_th, label_en, label_lo, ...)
รันครั้งเดียว: python scripts/migrate_program_settings.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine
from app.models import Base, ProgramSetting, Translation

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
    "foodcourt_id_placeholder": {"th": "สแกนหรือกรอก Marketplace ID (หักยอด)", "en": "Scan or enter Marketplace ID", "lo": "ສະແກນ ຫຼື ປ້ອນ Food Court ID", "my": "စကင်န်သို့မဟုတ်ထည့်သွင်း Food Court ID", "kh": "ស្កេន ឬបញ្ចូល Food Court ID", "ms": "Imbas atau masukkan Food Court ID", "shn": "တူၵ်းလဵၵ်း Food Court ID", "zh": "扫描或输入美食广场ID", "ru": "Сканируйте или введите ID фудкорта"},
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
    # หมายเหตุการพิมพ์ + คำอธิบายรูปภาพเมนู
    "print_note": {"th": "หมายเหตุ: การพิมพ์จาก Browser จะแสดงหน้าต่างพิมพ์หนึ่งครั้ง (ไม่สามารถส่งตรงไปเครื่องพิมพ์โดยไม่ถามได้) แนะนำให้ตั้งเครื่องพิมพ์ Thermal เป็นเครื่องพิมพ์หลักใน Windows เพื่อกดพิมพ์ได้เร็ว", "en": "Note: Browser printing shows a print dialog once (cannot send directly to printer without prompting). Recommend setting Thermal printer as default in Windows for faster printing.", "lo": "ຫມາຍເຫດ: ການພິມຈາກ Browser ຈະສະແດງຫນ້າຕ່າງພິມຄັ້ງດຽວ. ແນະນຳໃຫ້ຕັ້ງເຄື່ອງພິມ Thermal ເປັນເຄື່ອງພິມຫຼັກໃນ Windows.", "zh": "注意：浏览器打印会显示一次打印窗口（无法直接发送到打印机而不提示）。建议将热敏打印机设为 Windows 默认打印机以便快速打印。", "ru": "Примечание: печать из браузера показывает диалог один раз. Рекомендуется установить термопринтер по умолчанию в Windows."},
    "menu_image_source_desc": {"th": "Local = ไฟล์ดาวน์โหลดไว้ในเครื่อง, Server = image_url, Base64 = ใน DB", "en": "Local = file on device, Server = image_url, Base64 = in DB", "lo": "Local = ໄຟລ໌ໃນເຄື່ອງ, Server = image_url, Base64 = ໃນ DB", "zh": "Local = 本地文件, Server = image_url, Base64 = 数据库", "ru": "Local = файл на устройстве, Server = image_url, Base64 = в БД"},
    "menu_image_priority_local_first": {"th": "Local ก่อน → Server → Base64", "en": "Local first → Server → Base64", "lo": "Local ກ່ອນ → Server → Base64", "zh": "Local 优先 → Server → Base64", "ru": "Local → Server → Base64"},
    "menu_image_priority_server_first": {"th": "Server ก่อน → Local → Base64", "en": "Server first → Local → Base64", "lo": "Server ກ່ອນ → Local → Base64", "zh": "Server 优先 → Local → Base64", "ru": "Server → Local → Base64"},
    "menu_image_priority_base64_first": {"th": "Base64 ก่อน → Local → Server", "en": "Base64 first → Local → Server", "lo": "Base64 ກ່ອນ → Local → Server", "zh": "Base64 优先 → Local → Server", "ru": "Base64 → Local → Server"},
    "menu_image_priority_label": {"th": "ลำดับการเลือกแหล่งรูป (local, server, base64)", "en": "Image source priority (local, server, base64)", "lo": "ລຳດັບແຫຼ່ງຮູບ", "zh": "图片来源优先级 (local, server, base64)", "ru": "Приоритет источника изображения"},
    "menu_columns_desc": {"th": "จำนวนเมนูที่แสดงต่อแถวบน Store POS (Desktop)", "en": "Number of menu items per row on Store POS (Desktop)", "lo": "ຈຳນວນເມນູຕໍ່ແຖວ", "zh": "Store POS 每行显示的菜单数量（桌面版）", "ru": "Количество меню в строке"},
    "menu_columns_label": {"th": "จำนวนคอลัมน์เมนูต่อหน้า", "en": "Menu columns per page", "lo": "ຄໍລໍາມະນູເມນູ", "zh": "每页菜单列数", "ru": "Колонок меню"},
    # Admin Dashboard
    "admin_title": {"th": "Marketplace Management System", "en": "Marketplace Management System", "zh": "美食广场管理系统", "ru": "Система управления фудкортом"},
    "admin_subtitle": {"th": "Admin Dashboard - จัดการระบบทั้งหมดในหน้าเดียว", "en": "Admin Dashboard - Manage everything in one place", "zh": "管理面板 - 一站式管理", "ru": "Панель управления"},
    "tab_dashboard": {"th": "Dashboard", "en": "Dashboard", "zh": "仪表板", "ru": "Панель"},
    "tab_counter": {"th": "Counter", "en": "Counter", "zh": "柜台", "ru": "Касса"},
    "tab_payment": {"th": "Payment Hub", "en": "Payment Hub", "zh": "支付中心", "ru": "Платежи"},
    "tab_geo": {"th": "Geo Layout", "en": "Geo Layout", "zh": "布局", "ru": "Расположение"},
    "tab_refund": {"th": "Refund", "en": "Refund", "zh": "退款", "ru": "Возврат"},
    "tab_reports": {"th": "Reports", "en": "Reports", "zh": "报表", "ru": "Отчеты"},
    "tab_customers": {"th": "Customers", "en": "Customers", "zh": "客户", "ru": "Клиенты"},
    "tab_stores": {"th": "Stores", "en": "Stores", "zh": "店铺", "ru": "Магазины"},
    "tab_banking": {"th": "Banking", "en": "Banking", "zh": "银行/支付", "ru": "Банкинг"},
    "select_store": {"th": "เลือกร้านค้า", "en": "Select store", "zh": "选择店铺", "ru": "Выберите магазин"},
    "amount_baht": {"th": "จำนวนเงิน (บาท)", "en": "Amount (Baht)", "zh": "金额（泰铢）", "ru": "Сумма (бат)"},
    "store": {"th": "ร้านค้า", "en": "Store", "zh": "店铺", "ru": "Магазин"},
    "view_report": {"th": "ดูรายงาน", "en": "View report", "zh": "查看报表", "ru": "Просмотр отчета"},
    "no_data": {"th": "ยังไม่มีข้อมูล", "en": "No data yet", "zh": "暂无数据", "ru": "Нет данных"},
    # Customer
    "customer_title": {"th": "Marketplace - ลูกค้า", "en": "Marketplace - Customer", "zh": "美食广场 - 客户", "ru": "Фудкорт - Клиент"},
    "login_tab": {"th": "เข้าสู่ระบบ", "en": "Login", "zh": "登录", "ru": "Вход"},
    "register_tab": {"th": "ลงทะเบียน", "en": "Register", "zh": "注册", "ru": "Регистрация"},
    "phone_label": {"th": "เบอร์โทรศัพท์", "en": "Phone number", "zh": "电话号码", "ru": "Телефон"},
    "login_btn": {"th": "เข้าสู่ระบบ", "en": "Login", "zh": "登录", "ru": "Войти"},
    "balance_label": {"th": "ยอดเงินคงเหลือ", "en": "Balance", "zh": "余额", "ru": "Баланс"},
    "initial_amount": {"th": "จำนวนเงินเริ่มต้น", "en": "Initial amount", "zh": "初始金额", "ru": "Начальная сумма"},
    "payment_method": {"th": "วิธีชำระเงิน", "en": "Payment method", "zh": "支付方式", "ru": "Способ оплаты"},
    "status": {"th": "สถานะ", "en": "Status", "zh": "状态", "ru": "Статус"},
    # Customer QR
    "customer_qr_title": {"th": "Marketplace ID QR Code", "en": "Marketplace ID QR Code", "zh": "美食广场ID二维码", "ru": "QR код Food Court ID"},
    "foodcourt_id_label": {"th": "กรอก Marketplace ID", "en": "Enter Marketplace ID", "zh": "输入美食广场ID", "ru": "Введите Food Court ID"},
    "create_qr_btn": {"th": "สร้าง QR Code", "en": "Create QR Code", "zh": "生成二维码", "ru": "Создать QR код"},
    "how_to_use": {"th": "วิธีใช้งาน:", "en": "How to use:", "zh": "使用方法：", "ru": "Как использовать:"},
    "how_to_1": {"th": "กรอก Marketplace ID ของคุณ", "en": "Enter your Marketplace ID", "zh": "输入您的美食广场ID", "ru": "Введите ваш Food Court ID"},
    "how_to_2": {"th": "กดปุ่ม \"สร้าง QR Code\"", "en": "Click \"Create QR Code\" button", "zh": "点击「生成二维码」按钮", "ru": "Нажмите «Создать QR код»"},
    "how_to_3": {"th": "แสดง QR Code ให้ร้านค้าสแกน", "en": "Show QR Code for store to scan", "zh": "向店铺出示二维码供扫描", "ru": "Покажите QR код для сканирования"},
    "how_to_4": {"th": "ร้านค้าจะหักยอดเงินตามจำนวนที่กำหนด", "en": "Store will deduct the amount", "zh": "店铺将扣除相应金额", "ru": "Магазин спишет сумму"},
    "loading_text": {"th": "กำลังโหลดข้อมูล...", "en": "Loading...", "zh": "加载中...", "ru": "Загрузка..."},
    "custom_addon_label": {"th": "เมนูพิเศษกำหนดราคาเอง", "en": "Custom add-on (enter price)", "zh": "自定义加价", "ru": "Доп. цена"},
}

LOCALE_COL_MAP = {
    "th": "label_th", "en": "label_en", "lo": "label_lo", "my": "label_my",
    "kh": "label_kh", "ms": "label_ms", "shn": "label_shn", "zh": "label_zh", "ru": "label_ru",
}


def migrate():
    Base.metadata.create_all(bind=engine, tables=[ProgramSetting.__table__])

    from sqlalchemy.orm import Session
    db = Session(bind=engine)

    try:
        # 1. Migrate from Translation table if exists
        try:
            trans_rows = db.query(Translation).all()
            if trans_rows:
                by_key = {}
                for r in trans_rows:
                    if r.key not in by_key:
                        by_key[r.key] = {}
                    by_key[r.key][r.locale] = r.value

                for key, vals in by_key.items():
                    existing = db.query(ProgramSetting).filter(ProgramSetting.label_key == key).first()
                    if existing:
                        for loc, col in LOCALE_COL_MAP.items():
                            if loc in vals and vals[loc]:
                                setattr(existing, col, vals[loc])
                    else:
                        ps = ProgramSetting(label_key=key)
                        for loc, col in LOCALE_COL_MAP.items():
                            if loc in vals and vals[loc]:
                                setattr(ps, col, vals[loc])
                        db.add(ps)
                db.commit()
                print("Migration: Migrated", len(by_key), "labels from translations")
        except Exception as e:
            print("Migration: No translations table or error:", e)
            db.rollback()

        # 2. Seed from TRANSLATIONS if program_settings empty or missing keys
        existing_keys = {r.label_key for r in db.query(ProgramSetting.label_key).all()}
        added = 0
        for key, vals in TRANSLATIONS.items():
            if key not in existing_keys:
                ps = ProgramSetting(label_key=key)
                for loc, col in LOCALE_COL_MAP.items():
                    if loc in vals and vals[loc]:
                        setattr(ps, col, vals[loc])
                db.add(ps)
                existing_keys.add(key)
                added += 1
        if added > 0:
            db.commit()
            print("Migration: Seeded", added, "labels to program_settings")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
    print("Migration: program_settings done")
