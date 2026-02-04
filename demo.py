# demo.py
import os
import main

from database import init_db
from utils.demo_data import seed_demo_data

DB_PATH = "db/parc_auto.db"


# --------------------------------------------------
# RESET DATABASE
# --------------------------------------------------

def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️  Base supprimée")

    init_db(DB_PATH)
    print("🧱 Base initialisée")


# --------------------------------------------------
# RUN FULL DEMO
# --------------------------------------------------

def run():
    reset_db()

    print("🌱 Injection des données de démonstration")
    seed_demo_data(DB_PATH)

    print("\n🚀 Lancement de l'application\n")
    main.main()


if __name__ == "__main__":
    run()
