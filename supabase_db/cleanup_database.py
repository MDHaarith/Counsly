import os
import shutil
import sqlite3

def run_cleanup():
    db_path = "/home/mdhaarith/Documents/Counsly/counsly.db"
    backup_path = "/home/mdhaarith/Documents/Counsly/counsly_backup.db"

    # 1. Create a backup first
    print(f"Creating a backup of counsly.db to {backup_path}...")
    shutil.copy2(db_path, backup_path)
    print("Backup created successfully.")

    # 2. Connect to SQLite database
    print("\nConnecting to counsly.db...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 3. Enable foreign keys
    print("Enabling foreign keys...")
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 4. Pre-migration checks
    print("\n--- Running Pre-migration Audits ---")
    cursor.execute("PRAGMA integrity_check;")
    pre_integrity = cursor.fetchall()
    print("Pre-migration integrity check:", dict(pre_integrity[0]) if pre_integrity else "Unknown")

    cursor.execute("PRAGMA foreign_key_check;")
    pre_fk_issues = cursor.fetchall()
    print("Pre-migration foreign key issues:", len(pre_fk_issues))
    for issue in pre_fk_issues:
        print(dict(issue))

    # 5. Execute cleanup inside a transaction
    print("\nExecuting database cleanup transaction...")
    try:
        cursor.execute("BEGIN TRANSACTION;")

        # Drop unused/future-feature empty tables
        tables_to_drop = [
            "ai_guidance_log",
            "scraping_jobs",
            "admin_audit_log",
            "admin_update_log",
            "tnea_roll_numbers",
            "subscriptions",
            "client_error_log"
        ]

        for table in tables_to_drop:
            print(f"- Dropping table IF EXISTS `{table}`...")
            cursor.execute(f"DROP TABLE IF EXISTS `{table}`;")

        # Delete stale prediction metadata from data_freshness
        print("- Deleting stale 2026 prediction metadata from `data_freshness`...")
        cursor.execute("""
            DELETE FROM data_freshness
            WHERE dataset_key = 'cutoff_data_2026_predictions';
        """)

        conn.commit()
        print("Transaction committed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Transaction failed, rolled back changes! Error: {e}")
        conn.close()
        return

    # 6. Post-migration audits
    print("\n--- Running Post-migration Audits ---")
    cursor.execute("PRAGMA integrity_check;")
    post_integrity = cursor.fetchall()
    print("Post-migration integrity check:", dict(post_integrity[0]) if post_integrity else "Unknown")

    cursor.execute("PRAGMA foreign_key_check;")
    post_fk_issues = cursor.fetchall()
    print("Post-migration foreign key issues (empty is good):", len(post_fk_issues))
    for issue in post_fk_issues:
        print(dict(issue))

    conn.close()
    print("\nSQLite database cleanup completed successfully!")

if __name__ == "__main__":
    run_cleanup()
