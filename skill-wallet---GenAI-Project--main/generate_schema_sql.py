# File: generate_schema_sql.py
import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import engine
from app.database.base import Base

def main():
    # Force table creation
    print("Creating tables in sqlite database...")
    Base.metadata.create_all(bind=engine)
    
    # Connect and extract DDL
    db_file = "edugenie.db"
    if not os.path.exists(db_file):
        print(f"Error: {db_file} was not created!")
        return
        
    print(f"Connecting to {db_file}...")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Query sqlite_master to get DDL statements
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    
    # Get index creation SQL
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
    indexes = cursor.fetchall()
    
    schema_sql_content = "-- EduGenie Database Schema DDL (SQLite)\n"
    schema_sql_content += f"-- Generated on: {sqlite3.sqlite_version}\n\n"
    schema_sql_content += "PRAGMA foreign_keys = ON;\n\n"
    
    for name, sql in tables:
        if sql:
            schema_sql_content += f"-- Table: {name}\n"
            schema_sql_content += f"{sql};\n\n"
            
    schema_sql_content += "-- Indexes\n"
    for name, sql in indexes:
        if sql:
            schema_sql_content += f"{sql};\n\n"
            
    with open("schema.sql", "w", encoding="utf-8") as f:
        f.write(schema_sql_content)
        
    print("✔ schema.sql has been successfully generated in the project root.")
    conn.close()

if __name__ == "__main__":
    main()
