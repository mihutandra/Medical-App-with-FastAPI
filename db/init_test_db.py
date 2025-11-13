from db.tempdb import create_db_and_tables

if __name__ == "__main__":
    print("Creating tables in test database...")
    create_db_and_tables()
    print("Done.")
