"""
Creates all tables and loads the Goa reference dataset from CSVs in data/raw/ 

Run with:  python -m database.init_db
"""
from data.load_seed_from_csv import reset_and_seed

if __name__ == "__main__":
    reset_and_seed()