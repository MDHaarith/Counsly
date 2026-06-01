# Counsly Database Directory Map & Data Pipeline Boundaries

This directory manages the master database schema, seeding pipelines, and geocoded assets for the Counsly data-only MVP launch. To ensure clean boundaries and prevent navigation/indexing clutter, the folder is structured into **Active Runtime Pipelines** and **Archive Data Extractor Outputs**.

---

## 🚀 1. Active Runtime Pipelines (Production Surface)

These directories and files are actively used to provision and seed the Counsly database (`counsly.db`) in local development and production container setups.

*   [seed_data/](file:///home/mdhaarith/Documents/Counsly/supabase_db/seed_data/)
    *   Contains the canonical production master databases in JSON format (`colleges.json` and `college_geo.json`), representing the single source of truth for the TNEA 2027 college list and geocoded railway/bus transit points.
*   [schema.sql](file:///home/mdhaarith/Documents/Counsly/supabase_db/schema.sql)
    *   Defines the SQLite/PostgreSQL DDL schema (tables, unique constraints, and optimized indices) mapping user profiles, workspaces, choices, and transit metadata.
*   [seed_production.py](file:///home/mdhaarith/Documents/Counsly/supabase_db/seed_production.py)
    *   Database-agnostic master seeder utilizing SQLAlchemy transactions to load colleges, community cutoffs, transit points, and seat matrix quotas cleanly.
*   [cleanup_database.py](file:///home/mdhaarith/Documents/Counsly/supabase_db/supabase_db/cleanup_database.py)
    *   Audits, prunes obsolete prototype tables, and backs up database status in preparation for launching the data-only MVP.
*   [sync_db_to_json.py](file:///home/mdhaarith/Documents/Counsly/supabase_db/sync_db_to_json.py)
    *   Ingestion sync tool that parses corrected coordinates and geocoded transit distances from SQLite and updates the master JSON files to ensure absolute parity.

---

## 📂 2. Data Extractor Archive & Raw Sources (Offline Asset)

The [Data_Extractor/](file:///home/mdhaarith/Documents/Counsly/supabase_db/Data_Extractor/) subdirectory contains **offline scraping pipelines, historical raw source PDFs, and intermediate extraction outputs** from previous runs. 

> [!NOTE]
> These assets are preserved exclusively for historical audit trails and future PDF extraction runs. They are **never** called, loaded, or executed by the runtime FastAPI backend or Next.js frontend services.

### Archive Folders:
*   `Seat_Matrix/`, `General_Rank_List/`, `Pass_Percentage/`, `TFC/`: Contain official raw TNEA PDFs and parser scripts.
*   `data/`: Large intermediate CSV extracts and raw dataset aggregates.
*   `geo_integration/`: Historical GIS automation attempts and Go-based geolocation scripts.
