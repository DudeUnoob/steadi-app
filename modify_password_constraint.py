import os
from sqlmodel import Session
from sqlalchemy import text
from app.db.database import engine
from dotenv import load_dotenv


load_dotenv()

def modify_password_constraint():
    """
    Modify the password_hash column in the user table to allow NULL values
    """
    with Session(engine) as session:
        print("Modifying password_hash column to allow NULL values...")
        
        
        alter_column_sql = text("""
        ALTER TABLE "user" 
        ALTER COLUMN password_hash DROP NOT NULL;
        """)
        
        try:
            session.exec(alter_column_sql)
            session.commit()
            print("Successfully modified password_hash column to allow NULL values!")
        except Exception as e:
            print(f"Error modifying password_hash column: {str(e)}")
            session.rollback()

if __name__ == "__main__":
    modify_password_constraint() 