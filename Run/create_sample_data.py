"""
Script สำหรับสร้างข้อมูลตัวอย่าง 20 รายการ
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# โปรเจกต์จัดเป็น code/ + Run/ + Deploy/
root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.database import SessionLocal, engine, Base
from app.models import (
    Customer, CustomerBalance, Store, FoodCourtID,
    CounterTransaction, StoreTransaction, Transaction,
    PaymentMethod, TransactionStatus
)
from app.utils.store_token import generate_store_token
from app.services.payment_hub import PaymentHub
import json

# สร้าง tables ถ้ายังไม่มี
Base.metadata.create_all(bind=engine)

def create_sample_stores(db):
    """สร้างร้านค้าตัวอย่าง"""
    stores_data = [
        {"name": "ร้านอาหารไทย", "tax_id": "1234567890123"},
        {"name": "ร้านก๋วยเตี๋ยว", "tax_id": "1234567890124"},
        {"name": "ร้านข้าวผัด", "tax_id": "1234567890125"},
        {"name": "ร้านเครื่องดื่ม", "tax_id": "1234567890126"},
        {"name": "ร้านของหวาน", "tax_id": "1234567890127"},
        {"name": "ร้านส้มตำ", "tax_id": "1234567890128"},
        {"name": "ร้านข้าวมันไก่", "tax_id": "1234567890129"},
        {"name": "ร้านกะเพรา", "tax_id": "1234567890130"},
        {"name": "ร้านหมูกระทะ", "tax_id": "1234567890131"},
        {"name": "ร้านชาบู", "tax_id": "1234567890132"},
    ]
    
    stores = []
    created_count = 0
    skipped_count = 0
    
    for store_data in stores_data:
        # ตรวจสอบว่ามีร้านค้าอยู่แล้วหรือไม่
        existing = db.query(Store).filter(
            Store.name == store_data["name"]
        ).first()
        
        if existing:
            stores.append(existing)
            skipped_count += 1
        else:
            store = Store(
                name=store_data["name"],
                tax_id=store_data["tax_id"],
                crypto_enabled=random.choice([True, False]),
                contract_accepted=random.choice([True, False]),
                group_id=0,
                site_id=0,
                biller_id="011556400219809",  # Biller ID สำหรับทดสอบ
            )
            db.add(store)
            stores.append(store)
            created_count += 1

    db.commit()

    # เติม token ประจำร้านสำหรับทุกร้าน (รวมที่สร้างใหม่และที่มีอยู่แล้ว)
    for store in stores:
        if not store.token:
            store.token = generate_store_token(
                group_id=getattr(store, "group_id", 0) or 0,
                site_id=getattr(store, "site_id", 0) or 0,
                store_id=store.id,
                menu_id=0,
            )
    db.commit()

    print(f"✅ Created {created_count} new stores")
    if skipped_count > 0:
        print(f"ℹ️  Skipped {skipped_count} existing stores")
    print(f"📊 Total stores available: {len(stores)}")
    return stores

def create_sample_customers(db):
    """สร้างลูกค้าตัวอย่าง 40 ราย"""
    customers_data = [
        # รายการที่ 1-20
        {"phone": "0812345678", "name": "สมชาย ใจดี", "promptpay": "0812345678"},
        {"phone": "0823456789", "name": "สมหญิง รักดี", "promptpay": "0823456789"},
        {"phone": "0834567890", "name": "วิชัย เก่งมาก", "promptpay": "0834567890"},
        {"phone": "0845678901", "name": "มาลี สวยงาม", "promptpay": "0845678901"},
        {"phone": "0856789012", "name": "ประยุทธ์ ทำงานดี", "promptpay": "0856789012"},
        {"phone": "0867890123", "name": "สุรชัย รักการอ่าน", "promptpay": "0867890123"},
        {"phone": "0878901234", "name": "นภัสวรรณ ใจกว้าง", "promptpay": "0878901234"},
        {"phone": "0889012345", "name": "ธนพล เก่งกีฬา", "promptpay": "0889012345"},
        {"phone": "0890123456", "name": "กมลชนก รักธรรมชาติ", "promptpay": "0890123456"},
        {"phone": "0901234567", "name": "อรรถพล ทำงานหนัก", "promptpay": "0901234567"},
        {"phone": "0912345678", "name": "ปิยะมาศ สวยใส", "promptpay": "0912345678"},
        {"phone": "0923456789", "name": "ณัฐพล เก่งคอม", "promptpay": "0923456789"},
        {"phone": "0934567890", "name": "ศิริพร รักศิลปะ", "promptpay": "0934567890"},
        {"phone": "0945678901", "name": "ธีรพงษ์ เก่งภาษา", "promptpay": "0945678901"},
        {"phone": "0956789012", "name": "อรทัย รักดนตรี", "promptpay": "0956789012"},
        {"phone": "0967890123", "name": "วรพล ทำงานดี", "promptpay": "0967890123"},
        {"phone": "0978901234", "name": "กัญญา สวยงาม", "promptpay": "0978901234"},
        {"phone": "0989012345", "name": "ชาญชัย เก่งกีฬา", "promptpay": "0989012345"},
        {"phone": "0990123456", "name": "ปราณี รักการอ่าน", "promptpay": "0990123456"},
        {"phone": "0909876543", "name": "สมศักดิ์ ใจดี", "promptpay": "0909876543"},
        # รายการที่ 21-40 (เพิ่มใหม่)
        {"phone": "0612345678", "name": "อภิชัย รักการเรียน", "promptpay": "0612345678"},
        {"phone": "0623456789", "name": "กัลยาณี สวยงาม", "promptpay": "0623456789"},
        {"phone": "0634567890", "name": "ชัยวัฒน์ เก่งคณิต", "promptpay": "0634567890"},
        {"phone": "0645678901", "name": "ดวงใจ รักศิลปะ", "promptpay": "0645678901"},
        {"phone": "0656789012", "name": "ธีระ ทำงานดี", "promptpay": "0656789012"},
        {"phone": "0667890123", "name": "นันทนา ใจดี", "promptpay": "0667890123"},
        {"phone": "0678901234", "name": "บัณฑิต เก่งภาษา", "promptpay": "0678901234"},
        {"phone": "0689012345", "name": "ปราณี รักธรรมชาติ", "promptpay": "0689012345"},
        {"phone": "0690123456", "name": "มานะ ทำงานหนัก", "promptpay": "0690123456"},
        {"phone": "0601234567", "name": "รุ่งนภา สวยใส", "promptpay": "0601234567"},
        {"phone": "0613456789", "name": "วรวิทย์ เก่งคอม", "promptpay": "0613456789"},
        {"phone": "0624567890", "name": "ศิรินันท์ รักดนตรี", "promptpay": "0624567890"},
        {"phone": "0635678901", "name": "สุนิสา ใจกว้าง", "promptpay": "0635678901"},
        {"phone": "0646789012", "name": "อัครพงษ์ เก่งกีฬา", "promptpay": "0646789012"},
        {"phone": "0657890123", "name": "เกศรินทร์ รักการอ่าน", "promptpay": "0657890123"},
        {"phone": "0668901234", "name": "จิรศักดิ์ ทำงานดี", "promptpay": "0668901234"},
        {"phone": "0679012345", "name": "ชไมพร สวยงาม", "promptpay": "0679012345"},
        {"phone": "0680123456", "name": "ทวีศักดิ์ เก่งภาษา", "promptpay": "0680123456"},
        {"phone": "0691234567", "name": "นิรมล รักศิลปะ", "promptpay": "0691234567"},
        {"phone": "0602345678", "name": "พงศ์ศักดิ์ ใจดี", "promptpay": "0602345678"},
    ]
    
    customers = []
    created_count = 0
    skipped_count = 0
    
    for customer_data in customers_data:
        # ตรวจสอบว่ามีลูกค้าอยู่แล้วหรือไม่
        existing = db.query(Customer).filter(
            Customer.phone == customer_data["phone"]
        ).first()
        
        if existing:
            customers.append(existing)
            skipped_count += 1
        else:
            customer = Customer(
                phone=customer_data["phone"],
                name=customer_data["name"],
                promptpay_number=customer_data["promptpay"]
            )
            db.add(customer)
            customers.append(customer)
            created_count += 1
    
    db.commit()
    print(f"✅ Created {created_count} new customers")
    if skipped_count > 0:
        print(f"ℹ️  Skipped {skipped_count} existing customers")
    print(f"📊 Total customers available: {len(customers)}")
    return customers

def create_sample_foodcourt_ids(db, customers, stores):
    """สร้าง Food Court ID ตัวอย่าง 30 ชุด"""
    payment_hub = PaymentHub(db)
    payment_methods = [
        PaymentMethod.CASH,
        PaymentMethod.LINE_PAY,
        PaymentMethod.PROMPTPAY,
        PaymentMethod.APPLE_PAY,
        PaymentMethod.GOOGLE_PAY,
        PaymentMethod.SAMSUNG_PAY,
        PaymentMethod.CREDIT_CARD_VISA,
        PaymentMethod.CREDIT_CARD_MASTERCARD,
        PaymentMethod.TRUE_WALLET,
        PaymentMethod.SHOPEE_PAY,
        PaymentMethod.GRAB_PAY,
        PaymentMethod.PAYPAL,
        PaymentMethod.CRYPTO_BTC,
        PaymentMethod.CRYPTO_ETH,
        PaymentMethod.POINTS_THE1,
    ]
    
    foodcourt_ids = []
    amounts = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000]
    
    for i in range(30):
        customer = random.choice(customers) if customers else None
        payment_method = random.choice(payment_methods)
        amount = random.choice(amounts)
        
        payment_details = None
        if payment_method in [PaymentMethod.LINE_PAY, PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY, PaymentMethod.SAMSUNG_PAY]:
            payment_details = {"transaction_id": f"TXN{random.randint(100000, 999999)}"}
        elif payment_method in [PaymentMethod.CREDIT_CARD_VISA, PaymentMethod.CREDIT_CARD_MASTERCARD]:
            payment_details = {"last4": f"{random.randint(1000, 9999)}", "card_type": payment_method.value.split("_")[-1]}
        elif payment_method in [PaymentMethod.CRYPTO_BTC, PaymentMethod.CRYPTO_ETH]:
            payment_details = {"tx_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}"}
        elif payment_method == PaymentMethod.POINTS_THE1:
            payment_details = {"points_used": amount * 10, "points_balance": random.randint(10000, 50000)}
        
        foodcourt_id = payment_hub.exchange_to_foodcourt_id(
            amount=float(amount),
            payment_method=payment_method,
            payment_details=payment_details,
            counter_id=random.randint(1, 3),
            counter_user_id=random.randint(1, 5),
            customer_id=customer.id if customer else None
        )
        foodcourt_ids.append(foodcourt_id)
    
    db.commit()
    print(f"✅ Created {len(foodcourt_ids)} Food Court IDs")
    return foodcourt_ids

def create_sample_transactions(db, foodcourt_ids, stores):
    """สร้าง Transaction ตัวอย่าง"""
    transactions = []
    
    # ใช้ Food Court ID บางส่วน (ประมาณ 60-70% ของทั้งหมด)
    num_to_use = min(int(len(foodcourt_ids) * 0.65), len(foodcourt_ids))
    used_ids = random.sample(foodcourt_ids, num_to_use)
    
    for foodcourt_id in used_ids:
        # ใช้ที่ร้านต่างๆ
        num_stores = random.randint(1, 3)
        selected_stores = random.sample(stores, min(num_stores, len(stores)))
        
        remaining_balance = foodcourt_id.current_balance
        
        for store in selected_stores:
            if remaining_balance <= 0:
                break
            
            # ใช้เงินบางส่วน (30-80% ของยอดคงเหลือ)
            use_percentage = random.uniform(0.3, 0.8)
            amount = min(remaining_balance * use_percentage, remaining_balance)
            amount = round(amount, 2)
            
            if amount < 10:  # ถ้าน้อยกว่า 10 บาท ให้ใช้ทั้งหมด
                amount = remaining_balance
            
            payment_hub = PaymentHub(db)
            try:
                result = payment_hub.use_foodcourt_id(
                    foodcourt_id_str=foodcourt_id.foodcourt_id,
                    store_id=store.id,
                    amount=amount
                )
                remaining_balance = result["remaining_balance"]
                
                # ดึง transaction ที่สร้าง
                if result.get("transaction_id"):
                    transaction = db.query(Transaction).filter(
                        Transaction.id == result["transaction_id"]
                    ).first()
                    if transaction:
                        transactions.append(transaction)
            except Exception as e:
                print(f"⚠️  Error creating transaction: {e}")
    
    db.commit()
    print(f"✅ Created {len(transactions)} transactions")
    return transactions

def create_sample_balances(db, customers):
    """สร้างยอดเงินคงเหลือตัวอย่าง"""
    balances = []
    
    # สร้าง balance สำหรับลูกค้าบางคน
    selected_customers = random.sample(customers, min(10, len(customers)))
    
    for customer in selected_customers:
        # ตรวจสอบว่ามี balance อยู่แล้วหรือไม่
        existing = db.query(CustomerBalance).filter(
            CustomerBalance.customer_id == customer.id
        ).first()
        
        if not existing:
            balance = CustomerBalance(
                customer_id=customer.id,
                balance=round(random.uniform(100, 1000), 2)
            )
            db.add(balance)
            balances.append(balance)
    
    db.commit()
    print(f"✅ Created {len(balances)} customer balances")
    return balances

def main():
    """Main function"""
    print("=" * 60)
    print("Creating Sample Data")
    print("  - Customers: 40")
    print("  - Food Court IDs: 30")
    print("  - Stores: 10")
    print("=" * 60 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. สร้างร้านค้า
        print("1. Creating stores...")
        stores = create_sample_stores(db)
        
        # 2. สร้างลูกค้า
        print("\n2. Creating customers...")
        customers = create_sample_customers(db)
        
        # 3. สร้างยอดเงินคงเหลือ
        print("\n3. Creating customer balances...")
        balances = create_sample_balances(db, customers)
        
        # 4. สร้าง Food Court IDs
        print("\n4. Creating Food Court IDs...")
        foodcourt_ids = create_sample_foodcourt_ids(db, customers, stores)
        
        # 5. สร้าง Transactions
        print("\n5. Creating transactions...")
        transactions = create_sample_transactions(db, foodcourt_ids, stores)
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"✅ Stores: {len(stores)}")
        print(f"✅ Customers: {len(customers)}")
        print(f"✅ Customer Balances: {len(balances)}")
        print(f"✅ Food Court IDs: {len(foodcourt_ids)}")
        print(f"✅ Transactions: {len(transactions)}")
        print("=" * 60)
        
        print("\n📋 Sample Data Created Successfully!")
        print("\nExample Food Court IDs (showing 10 of 30):")
        for i, fc_id in enumerate(foodcourt_ids[:10], 1):
            print(f"  {i}. {fc_id.foodcourt_id} - {fc_id.initial_amount:,.2f} บาท ({fc_id.payment_method.value})")
        
        print("\nExample Customers (showing 10 of 40):")
        for i, customer in enumerate(customers[:10], 1):
            print(f"  {i}. {customer.name} ({customer.phone})")
        
        print("\nAll Stores (10 stores):")
        for i, store in enumerate(stores, 1):
            print(f"  {i}. {store.name}")
        
        print(f"\n📊 Statistics:")
        print(f"  - Total Food Court IDs: {len(foodcourt_ids)}")
        print(f"  - Total Customers: {len(customers)}")
        print(f"  - Total Stores: {len(stores)}")
        print(f"  - Total Transactions: {len(transactions)}")
        
        # สรุป Payment Methods
        payment_methods_count = {}
        for fc_id in foodcourt_ids:
            method = fc_id.payment_method.value
            payment_methods_count[method] = payment_methods_count.get(method, 0) + 1
        
        print(f"\n📈 Payment Methods Distribution:")
        for method, count in sorted(payment_methods_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {method}: {count} รายการ")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

