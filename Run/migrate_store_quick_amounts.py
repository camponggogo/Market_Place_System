"""
Migration script to create store_quick_amounts table
"""
import sys
import os

# โปรเจกต์จัดเป็น code/ + Run/ + Deploy/
_code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
sys.path.insert(0, _code_dir)

from sqlalchemy import create_engine, Table, Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text, MetaData, text
from sqlalchemy.sql import func
from app.config import DATABASE_URL

def migrate():
    engine = create_engine(DATABASE_URL)
    
    # Create table
    metadata = MetaData()
    
    store_quick_amounts = Table(
        'store_quick_amounts',
        metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('store_id', Integer, ForeignKey('stores.id'), nullable=False, index=True),
        Column('amount', Float, nullable=False),
        Column('label', String(50), nullable=True),
        Column('display_order', Integer, default=0, nullable=False),
        Column('is_active', Boolean, default=True, nullable=False),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), onupdate=func.now())
    )
    
    try:
        # Create table
        store_quick_amounts.create(engine, checkfirst=True)
        print("✅ Table 'store_quick_amounts' created successfully!")
        
        # Insert default quick amounts for existing stores
        with engine.connect() as conn:
            # Get all stores
            result = conn.execute(text("SELECT id FROM stores"))
            stores = result.fetchall()
            
            if stores:
                default_amounts = [50, 100, 200, 500]
                for store in stores:
                    store_id = store[0]
                    for idx, amount in enumerate(default_amounts):
                        try:
                            conn.execute(
                                text("INSERT INTO store_quick_amounts (store_id, amount, label, display_order, is_active) VALUES (:store_id, :amount, :label, :display_order, :is_active)"),
                                {
                                    "store_id": store_id,
                                    "amount": amount,
                                    "label": f"{amount} บาท",
                                    "display_order": idx,
                                    "is_active": True
                                }
                            )
                        except Exception as e:
                            print(f"⚠️  Could not insert default amount {amount} for store {store_id}: {e}")
                
                conn.commit()
                print(f"✅ Inserted default quick amounts for {len(stores)} stores")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    migrate()

