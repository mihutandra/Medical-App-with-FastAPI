
from db.session import create_db_and_tables

if __name__ == "__main__":
    print("Creating tables...")
    create_db_and_tables()
    print("Done.")
