import os
from sqlmodel import Session
from sqlalchemy import text
from app.db.database import engine
from dotenv import load_dotenv
import time


load_dotenv()

def add_supabase_id_column():
    """
    Add the supabase_id column to the user table
    """
    with Session(engine) as session:
        print("Adding supabase_id column to user table...")
        
       
        check_column_sql = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'user' AND column_name = 'supabase_id';
        """)
        
        result = session.exec(check_column_sql).all()
        if result:
            print("Column supabase_id already exists in user table. No action needed.")
            return
        
        
        add_column_sql = text("""
        ALTER TABLE "user" 
        ADD COLUMN supabase_id VARCHAR DEFAULT NULL UNIQUE;
        CREATE INDEX IF NOT EXISTS ix_user_supabase_id ON "user"(supabase_id);
        """)
        
        try:
            session.exec(add_column_sql)
            session.commit()
            print("Successfully added supabase_id column to user table!")
        except Exception as e:
            print(f"Error adding supabase_id column: {str(e)}")
            session.rollback()

if __name__ == "__main__":
    add_supabase_id_column() 