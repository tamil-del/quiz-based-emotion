import sqlite3

conn = sqlite3.connect('quiz.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("\n" + "=" * 60)
print("DATABASE TABLES:")
print("=" * 60)

for table in tables:
    table_name = table[0]
    print(f"\n{table_name}")
    print("-" * 60)
    
    # Get table structure
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    for col in columns:
        col_id, name, type_, not_null, default, pk = col
        pk_label = ' [PK]' if pk else ''
        print(f"  {name} ({type_}){pk_label}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  Total rows: {count}")

conn.close()
print("\n" + "=" * 60 + "\n")
