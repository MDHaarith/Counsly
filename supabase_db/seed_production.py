import os
import sys
import json
import csv
import re
from datetime import datetime, timezone
from sqlalchemy import insert, delete, text

# Ensure the root project folder is on python path so 'backend' is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.database import engine, SessionLocal
from backend.models import (
    Base, Branch, College, CollegeBranch, CommunitySeat,
    TFCLocation, CutoffData, IngestionAuditLog, DataFreshness
)

# Define absolute paths matching the environment
BASE_DIR = "/home/mdhaarith/Documents/Counsly"
SEED_DATA_DIR = os.path.join(BASE_DIR, "supabase_db/seed_data")

def clean_name(name: str) -> str:
    """Helper to clean names for robust geocoding lookup."""
    return re.sub(r'[^a-z0-9]', '', name.lower())

def classify_college_type(name: str) -> str:
    """Classify college type dynamically based on the PRD rules."""
    name_lower = name.lower()
    
    govt_keywords = [
        "university departments of anna university",
        "government college",
        "govt college",
        "university college of engineering",
        "annamalai university",
        "central electrochemical",
        "cipet"
    ]
    aided_keywords = [
        "psg college of technology",
        "coimbatore institute of technology",
        "thiagarajar college of engineering",
        "aided"
    ]
    
    if any(kw in name_lower for kw in govt_keywords):
        return "Govt"
    elif any(kw in name_lower for kw in aided_keywords):
        return "Aided"
    else:
        return "Self-Finance"

def main():
    print("--- COUNSLY PRODUCTION DATABASE SEEDER ---")
    print(f"Connecting to database target: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    
    start_time = datetime.now()
    
    # Initialize SQLAlchemy Session
    session = SessionLocal()
    
    try:
        # 1. Clear existing reference data tables in order of foreign key dependencies
        print("Clearing existing reference tables...")
        session.execute(delete(CutoffData))
        session.execute(delete(CommunitySeat))
        session.execute(delete(CollegeBranch))
        session.execute(delete(College))
        session.execute(delete(Branch))
        session.execute(delete(TFCLocation))
        session.commit()
        print("Reference tables cleared successfully.")
        
        # Freshness audit helper
        def log_audit(dataset, source, rows_ins, started, status, err=None):
            audit = IngestionAuditLog(
                dataset=dataset,
                source=source,
                rows_inserted=rows_ins,
                started_at=started,
                completed_at=datetime.now(timezone.utc),
                status=status,
                error_message=err
            )
            session.add(audit)
            session.commit()
            
        def update_freshness(key, count, notes):
            fresh = session.query(DataFreshness).filter_by(dataset_key=key).first()
            if not fresh:
                fresh = DataFreshness(dataset_key=key, last_refreshed=datetime.now(timezone.utc), row_count=count, notes=notes)
                session.add(fresh)
            else:
                fresh.last_refreshed = datetime.now(timezone.utc)
                fresh.row_count = count
                fresh.notes = notes
            session.commit()

        # 2. Ingest Branches
        print("Ingesting branches master data...")
        branch_started = datetime.now(timezone.utc)
        kept_branches = set()
        branches_file = os.path.join(SEED_DATA_DIR, "branches/branches.json")
        
        try:
            branch_map = {} # code -> {"name": name, "is_arch": is_arch}
            
            # Priority 1: Read all branches from branches.json
            with open(branches_file, "r") as f:
                branches_data = json.load(f)
            for b in branches_data:
                code = b["branch_code"].strip().upper()
                name = b["branch_name"].strip()
                is_arch = b.get("is_architecture", False)
                branch_map[code] = {"name": name, "is_arch": is_arch}
                
            # Priority 2: Scan seat matrix JSON for any missing branch codes
            seat_file = os.path.join(SEED_DATA_DIR, "community_seats/seat_matrix_2025_round_1.json")
            if os.path.exists(seat_file):
                with open(seat_file, "r") as f:
                    seat_data = json.load(f)
                for item in seat_data:
                    code = item["branch_code"].strip().upper()
                    name = item.get("branch_name", "").strip()
                    if name:
                        is_arch = "architecture" in name.lower() or "b.arch" in name.lower()
                        if code not in branch_map:
                            branch_map[code] = {"name": name, "is_arch": is_arch}
                        elif not branch_map[code]["name"] and name:
                            branch_map[code] = {"name": name, "is_arch": is_arch}
                            
            # Priority 3: Scan cutoffs CSV for any missing branch codes and map them
            MISSING_BRANCH_NAMES = {
                "BD": "BIOMEDICAL ENGINEERING (SS)",
                "CT": "COMPUTER TECHNOLOGY",
                "ES": "ENVIRONMENTAL ENGINEERING",
                "ET": "ELECTRONICS AND TELECOMMUNICATION ENGINEERING",
                "IX": "INSTRUMENTATION ENGINEERING (SS)",
                "MC": "MECHATRONICS ENGINEERING",
                "MH": "MECHATRONICS ENGINEERING (SS)",
                "NS": "NANO SCIENCE AND TECHNOLOGY",
                "PD": "PRODUCTION ENGINEERING (SS)",
                "PL": "PLASTIC TECHNOLOGY",
                "PS": "PRODUCTION ENGINEERING (SANDWICH)",
                "PU": "PRODUCTION ENGINEERING",
                "SE": "SOFTWARE ENGINEERING"
            }
            cutoff_file = os.path.join(SEED_DATA_DIR, "cutoff_data/cutoffs_2020_2025_training_ready.csv")
            if os.path.exists(cutoff_file):
                with open(cutoff_file, "r") as f:
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        if len(row) > 9:
                            code = row[9].strip().upper()
                            if code not in branch_map:
                                name = MISSING_BRANCH_NAMES.get(code, f"Branch {code}")
                                is_arch = "architecture" in name.lower() or "b.arch" in name.lower()
                                branch_map[code] = {"name": name, "is_arch": is_arch}
                                
            # Seed all gathered branches into the database using bulk insert
            branch_rows = []
            for code, info in sorted(branch_map.items()):
                name = info["name"]
                duration = 5 if info["is_arch"] else 4
                branch_rows.append({
                    "code": code,
                    "name": name,
                    "duration_years": duration
                })
                kept_branches.add(code)
                
            session.execute(insert(Branch), branch_rows)
            session.commit()
            log_audit("branches", "branches.json + dynamically_discovered", len(branch_rows), branch_started, "success")
            update_freshness("branches", len(branch_rows), f"Loaded {len(branch_rows)} dynamically discovered branch codes.")
            print(f"Ingested {len(branch_rows)} branches.")
        except Exception as e:
            session.rollback()
            print(f"Error seeding branches: {e}")
            log_audit("branches", "branches.json", 0, branch_started, "failed", str(e))
            raise e

        # 3. Ingest Colleges & College-Branch initial mappings
        print("Ingesting colleges master data...")
        college_started = datetime.now(timezone.utc)
        kept_colleges = set()
        added_college_branches = set()
        
        colleges_file = os.path.join(SEED_DATA_DIR, "colleges/colleges.json")
        geo_file = os.path.join(SEED_DATA_DIR, "colleges/college_geo.json")
        
        try:
            # Load geocoding lookup
            with open(geo_file, "r") as f:
                geo_data = json.load(f)
            
            geo_lookup = {}
            for entry in geo_data:
                orig = entry.get("original", "")
                if orig:
                    geo_lookup[clean_name(orig)] = {
                        "lat": entry.get("latitude"),
                        "lon": entry.get("longitude")
                    }
                    
            # Load colleges
            with open(colleges_file, "r") as f:
                colleges_data = json.load(f)
                
            college_rows = []
            college_branch_rows = []
            
            for c in colleges_data:
                # PRD: Exclude all architecture colleges
                name = c["College_Name"].strip()
                if "architecture" in name.lower() or ("planning" in name.lower() and "engineering" not in name.lower()):
                    continue
                    
                code = str(c["College_Code"]).strip()
                district = c["District"].strip()
                addr = c["Address"].strip() if c.get("Address") else None
                website = c["Website"].strip() if c.get("Website") else None
                
                # Geocoding lookup
                cleaned_col_name = clean_name(name)
                geo_match = geo_lookup.get(cleaned_col_name)
                lat = geo_match["lat"] if geo_match else None
                lon = geo_match["lon"] if geo_match else None
                coord_approx = False if geo_match else True
                
                # Type classification
                col_type = classify_college_type(name)
                
                # Hostel/transport parsing
                boys_h = c.get("Hostel_Boys_Permanent_or_Rental")
                girls_h = c.get("Hostel_Girls_Permanent_or_Rental")
                hostel = bool(
                    (boys_h and boys_h != "-" and boys_h.lower() not in ("no", "nil")) or
                    (girls_h and girls_h != "-" and girls_h.lower() not in ("no", "nil"))
                )
                
                trans = c.get("Transport_Facilities")
                transport = bool(trans and trans.lower() in ("yes", "available"))
                
                # Autonomous and NBA
                is_auto = bool(c.get("Autonomous_Status", "").strip().lower() == "autonomous")
                
                courses = c.get("courses", [])
                has_nba = any(course.get("NBA_Accredited", "").strip().lower() == "yes" for course in courses)
                
                # Railway station and distance
                rail_station = c.get("Nearest_Railway_Station")
                rail_station = rail_station.strip() if rail_station else None
                
                rail_dist = None
                raw_dist = c.get("Distance_in_KMS_from_Nearest_Railway_Station")
                if raw_dist is not None and raw_dist != "-":
                    try:
                        rail_dist = float(raw_dist)
                    except Exception:
                        pass
                        
                # Fees calculation
                def parse_fee(val):
                    if val is None or val == "-":
                        return 0
                    try:
                        return int(float(str(val).replace(",", "").strip()))
                    except Exception:
                        return 0
                
                room = parse_fee(c.get("Room_Rent"))
                elec = parse_fee(c.get("Electricity_Charges"))
                caution = parse_fee(c.get("Caution_Deposit"))
                estab = parse_fee(c.get("Establishment_Charges"))
                adm = parse_fee(c.get("Admission_Fees"))
                annual_fee = room + elec + caution + estab + adm
                
                # Placement rate
                placement_str = c.get("Placement_Record")
                placement_pct = 0.0
                if placement_str and placement_str != "-":
                    try:
                        placement_pct = float(str(placement_str).replace("%", "").strip())
                    except Exception:
                        pass
                
                college_rows.append({
                    "code": code,
                    "name": name,
                    "district": district,
                    "type": col_type,
                    "address": addr,
                    "latitude": lat,
                    "longitude": lon,
                    "hostel_available": hostel,
                    "transport_available": transport,
                    "website": website,
                    "is_autonomous": is_auto,
                    "nba_accredited": has_nba,
                    "coordinates_approximate": coord_approx,
                    "nearest_railway_station": rail_station,
                    "nearest_railway_distance_km": rail_dist,
                    "fee_structure_annual": annual_fee if annual_fee > 0 else None,
                    "placement_rate_pct": placement_pct,
                    "details_raw": json.dumps(c)
                })
                
                kept_colleges.add(code)
                
                # Setup College courses mappings
                for crs in courses:
                    b_code = crs["Branch_Code"].strip().upper()
                    if b_code in kept_branches:
                        intake = None
                        try:
                            intake = int(crs["Approved_Intake"])
                        except Exception:
                            pass
                            
                        yr_start = None
                        try:
                            yr_start = int(crs["Year_Starting"])
                        except Exception:
                            pass
                            
                        nba_crs = bool(crs.get("NBA_Accredited", "").strip().lower() == "yes")
                        
                        college_branch_rows.append({
                            "college_code": code,
                            "branch_code": b_code,
                            "approved_intake": intake,
                            "year_starting": yr_start,
                            "nba_accredited": nba_crs
                        })
                        added_college_branches.add((code, b_code))
            
            # Bulk inserts
            session.execute(insert(College), college_rows)
            session.execute(insert(CollegeBranch), college_branch_rows)
            session.commit()
            
            log_audit("colleges", "colleges.json", len(college_rows), college_started, "success")
            update_freshness("colleges", len(college_rows), f"Loaded {len(college_rows)} colleges and {len(college_branch_rows)} branch associations.")
            print(f"Ingested {len(college_rows)} colleges and {len(college_branch_rows)} college-branch mappings.")
        except Exception as e:
            session.rollback()
            print(f"Error seeding colleges: {e}")
            log_audit("colleges", "colleges.json", 0, college_started, "failed", str(e))
            raise e

        # 4. Ingest Seat Matrix (Community Seats)
        print("Ingesting seat matrix (community seats)...")
        seat_started = datetime.now(timezone.utc)
        seat_file = os.path.join(SEED_DATA_DIR, "community_seats/seat_matrix_2025_round_1.json")
        
        try:
            with open(seat_file, "r") as f:
                seat_data = json.load(f)
                
            seat_rows = []
            fallback_cb_rows = []
            
            for item in seat_data:
                c_code = str(item["college_code"]).strip()
                b_code = item["branch_code"].strip().upper()
                
                if c_code in kept_colleges and b_code in kept_branches:
                    # Ensure mapping exists in college_branches first
                    if (c_code, b_code) not in added_college_branches:
                        fallback_cb_rows.append({
                            "college_code": c_code,
                            "branch_code": b_code,
                            "approved_intake": item.get("total", 0),
                            "nba_accredited": False
                        })
                        added_college_branches.add((c_code, b_code))
                        
                    seat_rows.append({
                        "college_code": c_code,
                        "branch_code": b_code,
                        "oc": item.get("oc", 0),
                        "bc": item.get("bc", 0),
                        "bcm": item.get("bcm", 0),
                        "mbc": item.get("mbc", 0),
                        "sc": item.get("sc", 0),
                        "sca": item.get("sca", 0),
                        "st": item.get("st", 0),
                        "total": item.get("total", 0)
                    })
            
            # Bulk inserts
            if fallback_cb_rows:
                session.execute(insert(CollegeBranch), fallback_cb_rows)
            session.execute(insert(CommunitySeat), seat_rows)
            session.commit()
            
            log_audit("community_seats", "seat_matrix_2025_round_1.json", len(seat_rows), seat_started, "success")
            update_freshness("community_seats", len(seat_rows), f"Loaded {len(seat_rows)} seat matrix mappings. Created {len(fallback_cb_rows)} fallback branch mappings.")
            print(f"Ingested {len(seat_rows)} seat matrix records.")
        except Exception as e:
            session.rollback()
            print(f"Error seeding seat matrix: {e}")
            log_audit("community_seats", "seat_matrix_2025_round_1.json", 0, seat_started, "failed", str(e))
            raise e

        # 5. Ingest TFC Locations
        print("Ingesting facilitation center (TFC) locations...")
        tfc_started = datetime.now(timezone.utc)
        tfc_file = os.path.join(SEED_DATA_DIR, "tfc_locations/tfc_locations.json")
        
        try:
            with open(tfc_file, "r") as f:
                tfc_data = json.load(f)
                
            tfc_rows = []
            for item in tfc_data:
                tfc_rows.append({
                    "tfc_id": item["tfc_number"],
                    "centre_name": item["centre_name"].strip(),
                    "district": item["district"].strip(),
                    "address": item["full_address"].strip(),
                    "phone": None,
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "google_maps_url": item["google_maps_url"]
                })
                
            session.execute(insert(TFCLocation), tfc_rows)
            session.commit()
            
            log_audit("tfc_locations", "tfc_locations.json", len(tfc_rows), tfc_started, "success")
            update_freshness("tfc_locations", len(tfc_rows), f"Loaded {len(tfc_rows)} TFC locations.")
            print(f"Ingested {len(tfc_rows)} TFC locations.")
        except Exception as e:
            session.rollback()
            print(f"Error seeding TFCs: {e}")
            log_audit("tfc_locations", "tfc_locations.json", 0, tfc_started, "failed", str(e))
            raise e

        # 6. Ingest Cutoff Data (Streaming Aggregation)
        print("Ingesting historical and active cutoff data...")
        cutoff_started = datetime.now(timezone.utc)
        cutoff_file = os.path.join(SEED_DATA_DIR, "cutoff_data/cutoffs_2020_2025_training_ready.csv")
        
        try:
            print("Performing streaming aggregation over 550,000 records...")
            cutoff_groups = {}
            processed_lines = 0
            
            with open(cutoff_file, "r") as f:
                reader = csv.reader(f)
                header = next(reader)
                
                for row in reader:
                    try:
                        processed_lines += 1
                        year = int(row[0])
                        round_num = int(row[1])
                        mark = float(row[5])
                        rank = int(float(row[6]))
                        
                        # Auto-detect and fix swapped mark/rank for 2020 records
                        if mark > 200.0 and rank <= 200:
                            mark, rank = rank, int(mark)
                        student_comm = row[7].strip().upper()
                        coll_code = str(int(row[8])) # normalization to strip leading zeros
                        branch = row[9].strip().upper()
                        allotted_cat = row[10].strip().upper()
                        
                        # Filtering
                        if coll_code not in kept_colleges or branch not in kept_branches:
                            continue
                            
                        # Standardize quota
                        quota = allotted_cat if allotted_cat in ('OC', 'BC', 'BCM', 'MBC', 'SC', 'SCA', 'ST') else student_comm
                        if quota not in ('OC', 'BC', 'BCM', 'MBC', 'SC', 'SCA', 'ST'):
                            continue
                            
                        key = (coll_code, branch, quota, year, round_num)
                        if key not in cutoff_groups:
                            cutoff_groups[key] = {
                                "min_mark": mark,
                                "max_rank": rank,
                                "seats_allotted": 1
                            }
                        else:
                            stats = cutoff_groups[key]
                            if mark < stats["min_mark"]:
                                stats["min_mark"] = mark
                            if rank > stats["max_rank"]:
                                stats["max_rank"] = rank
                            stats["seats_allotted"] += 1
                    except Exception:
                        continue
                        
            print(f"Grouping complete. Found {len(cutoff_groups)} aggregate cutoff rows.")
            
            cutoff_rows = []
            for key, stats in cutoff_groups.items():
                coll_code, branch, quota, year, round_num = key
                cutoff_rows.append({
                    "college_code": coll_code,
                    "branch_code": branch,
                    "community": quota,
                    "year": year,
                    "round_number": round_num,
                    "cutoff_mark": stats["min_mark"],
                    "cutoff_rank": stats["max_rank"],
                    "seats_allotted": stats["seats_allotted"]
                })
                
            print(f"Bulk inserting {len(cutoff_rows)} rows to cutoff_data...")
            
            # Batch inserts to prevent database locks or memory overflows
            batch_size = 10000
            for idx in range(0, len(cutoff_rows), batch_size):
                batch = cutoff_rows[idx : idx + batch_size]
                session.execute(insert(CutoffData), batch)
                session.commit()
                
            log_audit("cutoff_data", "cutoffs_2020_2025_training_ready.csv", len(cutoff_rows), cutoff_started, "success")
            update_freshness("cutoff_data", len(cutoff_rows), f"Aggregated {processed_lines} raw rows into {len(cutoff_rows)} cutoff statistics.")
            print(f"Ingested {len(cutoff_rows)} cutoff data rows.")
        except Exception as e:
            session.rollback()
            print(f"Error seeding cutoffs: {e}")
            log_audit("cutoff_data", "cutoffs_2020_2025_training_ready.csv", 0, cutoff_started, "failed", str(e))
            raise e
            
        elapsed = datetime.now() - start_time
        print(f"\n--- PRODUCTION SEEDING SYSTEM COMPLETED SUCCESSFULLY IN {elapsed.total_seconds():.2f}s ---")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()
