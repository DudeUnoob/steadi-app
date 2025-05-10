import os
from sqlmodel import Session
from sqlalchemy import text
from app.db.database import engine
from dotenv import load_dotenv


load_dotenv()

def create_skualias_table():
    """
    Create the skualias table directly with SQL
    """
    with Session(engine) as session:
        print("Creating skualias table...")
        
        
        create_table_sql = text("""
        CREATE TABLE IF NOT EXISTS skualias (
            id UUID PRIMARY KEY,
            alias_sku VARCHAR NOT NULL,
            canonical_sku VARCHAR NOT NULL REFERENCES product(sku),
            notes TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            user_id UUID NOT NULL REFERENCES "user"(id)
        );
        CREATE INDEX IF NOT EXISTS idx_skualias_alias_sku ON skualias(alias_sku);
        CREATE INDEX IF NOT EXISTS idx_skualias_canonical_sku ON skualias(canonical_sku);
        CREATE INDEX IF NOT EXISTS idx_skualias_user_id ON skualias(user_id);
        """)
        
        try:
            session.exec(create_table_sql)
            session.commit()
            print("Successfully created skualias table!")
        except Exception as e:
            print(f"Error creating skualias table: {str(e)}")
            session.rollback()

if __name__ == "__main__":
    create_skualias_table() 