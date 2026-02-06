# Add payment gateway provider columns to banking_profiles (Omise, Stripe, MPay, provider_type)
# Run from project root: python Run/migrate_banking_profiles_gateway_providers.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from sqlalchemy import text
from app.database import engine

COLUMNS = [
    ("provider_type", "VARCHAR(32) NULL"),
    ("omise_public_key", "VARCHAR(255) NULL"),
    ("omise_secret_key", "VARCHAR(255) NULL"),
    ("omise_webhook_secret", "VARCHAR(255) NULL"),
    ("stripe_secret_key", "VARCHAR(255) NULL"),
    ("stripe_publishable_key", "VARCHAR(255) NULL"),
    ("stripe_webhook_secret", "VARCHAR(255) NULL"),
    ("mpay_merchant_id", "VARCHAR(128) NULL"),
    ("mpay_api_key", "VARCHAR(255) NULL"),
    ("mpay_webhook_secret", "VARCHAR(255) NULL"),
]

def main():
    with engine.connect() as conn:
        for col_name, col_def in COLUMNS:
            try:
                conn.execute(text(f"ALTER TABLE banking_profiles ADD COLUMN {col_name} {col_def}"))
                conn.commit()
                print(f"  + {col_name}")
            except Exception as e:
                if "Duplicate column" in str(e) or "already exists" in str(e).lower():
                    print(f"  (skip {col_name})")
                else:
                    raise
    print("Done.")

if __name__ == "__main__":
    main()
