import psycopg2
from psycopg2 import OperationalError
import os
from dotenv import load_dotenv

def test_connection():
    """Test database connection with environment variables"""
    # Load environment variables
    load_dotenv()
    
    # Get connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("Attempting to connect with parameters:")
    for key, value in db_params.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(value) if value else 'Not set'}")
        else:
            print(f"  {key}: {value}")
    
    try:
        # Attempt to connect
        conn = psycopg2.connect(**db_params)
        print("\n✅ Successfully connected to the database!")
        
        # Test a simple query
        with conn.cursor() as cur:
            cur.execute('SELECT version()')
            db_version = cur.fetchone()
            print(f"\nDatabase version: {db_version[0]}")
            
            # List all databases
            cur.execute('SELECT datname FROM pg_database;')
            databases = [db[0] for db in cur.fetchall()]
            print("\nAvailable databases:", ', '.join(databases))
            
        return True
        
    except OperationalError as e:
        print(f"\n❌ Error connecting to the database: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is running")
        print("2. Verify your database credentials in .env file")
        print("3. Check if the database exists")
        print("4. Verify the user has proper permissions")
        print("5. Check if the port is correct (default is 5432)")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("\nConnection closed.")

if __name__ == "__main__":
    test_connection()
