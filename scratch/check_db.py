import os
import sys
from dotenv import load_dotenv

# Ensure we can load configuration and modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import Config

try:
    import MySQLdb
    from MySQLdb.cursors import DictCursor
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()
    import MySQLdb
    from MySQLdb.cursors import DictCursor

def check():
    print("Connecting to database...")
    connect_args = {
        'host': Config.MYSQL_HOST,
        'user': Config.MYSQL_USER,
        'passwd': Config.MYSQL_PASSWORD,
        'db': Config.MYSQL_DB,
        'port': Config.MYSQL_PORT,
        'charset': getattr(Config, 'MYSQL_CHARSET', 'utf8mb4'),
        'cursorclass': DictCursor
    }
    if getattr(Config, 'MYSQL_SSL_CA', None):
        connect_args['ssl'] = {'ca': Config.MYSQL_SSL_CA}
    db = MySQLdb.connect(**connect_args)
    cur = db.cursor()
    
    # 1. Connection variables
    print("\n--- Connection Charset Variables ---")
    cur.execute("SHOW VARIABLES LIKE 'character_set_%'")
    for row in cur.fetchall():
        print(f"{row['Variable_name']}: {row['Value']}")
        
    print("\n--- Connection Collation Variables ---")
    cur.execute("SHOW VARIABLES LIKE 'collation_%'")
    for row in cur.fetchall():
        print(f"{row['Variable_name']}: {row['Value']}")

    # 2. Database default charset
    print("\n--- Database Default Charset ---")
    cur.execute("SELECT @@character_set_database, @@collation_database")
    row = cur.fetchone()
    print(row)

    # 3. Table charsets
    print("\n--- Table Charsets ---")
    cur.execute("""
        SELECT TABLE_NAME, TABLE_COLLATION 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
    """, (Config.MYSQL_DB,))
    for row in cur.fetchall():
        print(f"{row['TABLE_NAME']}: {row['TABLE_COLLATION']}")

    # 4. Column charsets (especially for goals and notifications)
    print("\n--- Columns Charsets ---")
    cur.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND DATA_TYPE IN ('varchar', 'text', 'mediumtext', 'longtext')
    """, (Config.MYSQL_DB,))
    for row in cur.fetchall():
        print(f"{row['TABLE_NAME']}.{row['COLUMN_NAME']}: {row['CHARACTER_SET_NAME']} / {row['COLLATION_NAME']}")

    cur.close()
    db.close()

if __name__ == '__main__':
    check()
