import csv
from datetime import datetime, timezone
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, delete
from typing import List, Optional
from backend.database import get_db
from backend.models import User, Workspace, UserCollegePreference, College, Branch, ShortlistSnapshot, ShortlistSnapshotItem, WorkspaceActivity, CollegeBranch
from backend.schemas import ChoiceItemResponse, ChoiceItemCreate, ReorderRequest, SnapshotCreate, SnapshotResponse
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/choices", tags=["choices"])

@router.get("/", response_model=List[ChoiceItemResponse])
def get_choices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    preferences = db.query(UserCollegePreference).filter(
        UserCollegePreference.workspace_id == ws.id
    ).order_by(UserCollegePreference.priority.asc()).all()
    
    response = []
    for pref in preferences:
        college = db.query(College).filter(College.code == pref.college_code).first()
        branch = db.query(Branch).filter(Branch.code == pref.branch_code).first()
        
        college_name = college.name if college else "Unknown College"
        branch_name = branch.name if branch else "Unknown Branch"
        
        response.append(ChoiceItemResponse(
            id=pref.id,
            college_code=pref.college_code,
            branch_code=pref.branch_code,
            priority=pref.priority,
            category=pref.category,
            notes=pref.notes,
            college_name=college_name,
            branch_name=branch_name,
            fee_structure_annual=college.fee_structure_annual if college else None,
            placement_rate_pct=college.placement_rate_pct if college else None
        ))
        
    return response

@router.post("/", response_model=ChoiceItemResponse)
def add_choice(req: ChoiceItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    # Check 300 limit
    count = db.query(UserCollegePreference).filter(UserCollegePreference.workspace_id == ws.id).count()
    if count >= 300:
        raise HTTPException(status_code=400, detail="Choice list has reached the absolute TNEA maximum limit of 300 selections.")
        
    college = db.query(College).filter(College.code == req.college_code).first()
    branch = db.query(Branch).filter(Branch.code == req.branch_code).first()
    if not college or not branch:
        raise HTTPException(status_code=404, detail="Invalid college or branch code specified")
        
    # Next priority index
    new_priority = count + 1
    
    pref = UserCollegePreference(
        workspace_id=ws.id,
        preference_group="primary",
        priority=new_priority,
        college_code=req.college_code,
        branch_code=req.branch_code,
        category=req.category or "Moderate",
        notes=req.notes
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    
    return ChoiceItemResponse(
        id=pref.id,
        college_code=pref.college_code,
        branch_code=pref.branch_code,
        priority=pref.priority,
        category=pref.category,
        notes=pref.notes,
        college_name=college.name,
        branch_name=branch.name,
        fee_structure_annual=college.fee_structure_annual,
        placement_rate_pct=college.placement_rate_pct
    )

@router.put("/reorder")
def reorder_choices(req: ReorderRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    # Atomic wipe & batch rewrite to prevent conflicts in sequential indices
    updates = req.priorities
    if not updates:
        raise HTTPException(status_code=400, detail="Priorities list cannot be empty")
        
    # Verify bounds
    if len(updates) > 300:
        raise HTTPException(status_code=400, detail="Cannot exceed maximum of 300 items")

    # Pre-validate all college and branch codes to ensure database integrity
    college_codes = {item.college_code for item in updates}
    branch_codes = {item.branch_code for item in updates}
    
    existing_colleges = db.query(College.code).filter(College.code.in_(college_codes)).all()
    existing_college_codes = {c[0] for c in existing_colleges}
    
    existing_branches = db.query(Branch.code).filter(Branch.code.in_(branch_codes)).all()
    existing_branch_codes = {b[0] for b in existing_branches}
    
    for item in updates:
        if item.college_code not in existing_college_codes:
            raise HTTPException(status_code=400, detail=f"Invalid college code: {item.college_code}")
        if item.branch_code not in existing_branch_codes:
            raise HTTPException(status_code=400, detail=f"Invalid branch code: {item.branch_code}")
        
    # Wipe existing
    db.execute(delete(UserCollegePreference).where(UserCollegePreference.workspace_id == ws.id))
    
    # Bulk insert updated ordering
    inserted_prefs = []
    for index, item in enumerate(updates, start=1):
        pref = UserCollegePreference(
            workspace_id=ws.id,
            preference_group="primary",
            priority=index,
            college_code=item.college_code,
            branch_code=item.branch_code,
            category=item.category or "Moderate",
            notes=item.notes
        )
        db.add(pref)
        inserted_prefs.append(pref)
        
    # Log reorder event
    activity = WorkspaceActivity(
        workspace_id=ws.id,
        event_type="choices_reordered",
        summary=f"Reordered engineering choice list. Current total selections: {len(updates)}.",
        created_at=datetime.now(timezone.utc)
    )
    db.add(activity)
    
    db.commit()
    return {"success": True, "message": "Engineering choice list reordered successfully."}

@router.delete("/{pref_id}")
def delete_choice(pref_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    target = db.query(UserCollegePreference).filter(
        and_(
            UserCollegePreference.id == pref_id,
            UserCollegePreference.workspace_id == ws.id
        )
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Choice preference item not found")
        
    target_priority = target.priority
    db.delete(target)
    db.flush()
    
    # Shift priorities of all items that were below it
    subsequent_items = db.query(UserCollegePreference).filter(
        and_(
            UserCollegePreference.workspace_id == ws.id,
            UserCollegePreference.priority > target_priority
        )
    ).order_by(UserCollegePreference.priority.asc()).all()
    
    for idx, item in enumerate(subsequent_items):
        item.priority = target_priority + idx
        
    db.commit()
    return {"success": True, "message": "Choice removed and subsequent priorities shifted successfully."}

@router.put("/{pref_id}")
def update_choice_details(pref_id: int, category: Optional[str] = None, notes: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    pref = db.query(UserCollegePreference).filter(
        and_(
            UserCollegePreference.id == pref_id,
            UserCollegePreference.workspace_id == ws.id
        )
    ).first()
    
    if not pref:
        raise HTTPException(status_code=404, detail="Choice item not found")
        
    if category is not None:
        if category not in ["Safe", "Moderate", "Ambitious"]:
            raise HTTPException(status_code=400, detail="Invalid preference category classification")
        pref.category = category
        pref.category_override = True
        
    if notes is not None:
        pref.notes = notes
        
    db.commit()
    return {"success": True, "message": "Choice metadata updated successfully."}

# --- SNAPSHOT ROUTES ---
@router.post("/snapshots", response_model=SnapshotResponse)
def create_snapshot(req: SnapshotCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    # Get current choices
    choices = db.query(UserCollegePreference).filter(
        UserCollegePreference.workspace_id == ws.id
    ).all()
    
    if not choices:
        raise HTTPException(status_code=400, detail="Cannot snapshot an empty choice list")
        
    import uuid
    snapshot_id = str(uuid.uuid4())
    snapshot = ShortlistSnapshot(
        id=snapshot_id,
        workspace_id=ws.id,
        title=req.title
    )
    db.add(snapshot)
    
    for item in choices:
        snap_item = ShortlistSnapshotItem(
            snapshot_id=snapshot_id,
            priority=item.priority,
            college_code=item.college_code,
            branch_code=item.branch_code,
            category=item.category,
            notes=item.notes
        )
        db.add(snap_item)
        
    # Log snapshot activity
    activity = WorkspaceActivity(
        workspace_id=ws.id,
        event_type="snapshot_saved",
        summary=f"Saved choice list snapshot: '{req.title}' containing {len(choices)} choices.",
        created_at=datetime.now(timezone.utc)
    )
    db.add(activity)
    
    db.commit()
    
    return SnapshotResponse(
        id=snapshot.id,
        title=snapshot.title,
        created_at=snapshot.created_at,
        item_count=len(choices)
    )

@router.get("/snapshots", response_model=List[SnapshotResponse])
def list_snapshots(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    snaps = db.query(ShortlistSnapshot).filter(
        ShortlistSnapshot.workspace_id == ws.id
    ).order_by(ShortlistSnapshot.created_at.desc()).all()
    
    response = []
    for s in snaps:
        count = db.query(ShortlistSnapshotItem).filter(ShortlistSnapshotItem.snapshot_id == s.id).count()
        response.append(SnapshotResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            item_count=count
        ))
    return response

@router.post("/snapshots/{snapshot_id}/restore")
def restore_snapshot(snapshot_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    snapshot = db.query(ShortlistSnapshot).filter(
        and_(
            ShortlistSnapshot.id == snapshot_id,
            ShortlistSnapshot.workspace_id == ws.id
        )
    ).first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Saved snapshot not found")
        
    snap_items = db.query(ShortlistSnapshotItem).filter(
        ShortlistSnapshotItem.snapshot_id == snapshot_id
    ).order_by(ShortlistSnapshotItem.priority.asc()).all()
    
    if not snap_items:
        raise HTTPException(status_code=400, detail="Snapshot contains no items")
        
    # Clear current
    db.execute(delete(UserCollegePreference).where(UserCollegePreference.workspace_id == ws.id))
    
    # Restore from snapshot items
    for item in snap_items:
        pref = UserCollegePreference(
            workspace_id=ws.id,
            preference_group="primary",
            priority=item.priority,
            college_code=item.college_code,
            branch_code=item.branch_code,
            category=item.category,
            notes=item.notes
        )
        db.add(pref)
        
    activity = WorkspaceActivity(
        workspace_id=ws.id,
        event_type="snapshot_restored",
        summary=f"Restored choice list snapshot: '{snapshot.title}' with {len(snap_items)} choices.",
        created_at=datetime.now(timezone.utc)
    )
    db.add(activity)
    
    db.commit()
    return {"success": True, "message": f"Successfully restored shortlist snapshot '{snapshot.title}'."}

# --- CSV IMPORT ENDPOINT ---
@router.post("/upload")
async def upload_choices_csv(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
        
    # Enforce maximum file size of 1MB to prevent server memory exhaustion
    max_file_size = 1 * 1024 * 1024  # 1MB
    chunk_size = 8192
    total_read = 0
    content_chunks = []
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > max_file_size:
            raise HTTPException(status_code=400, detail="File size exceeds the limit of 1MB.")
        content_chunks.append(chunk)
    content = b"".join(content_chunks)

    # Robust UTF-8 with latin-1 fallback encoding decoding
    try:
        string_data = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            string_data = content.decode("latin-1")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid file encoding. Only UTF-8 or standard ASCII encoded CSVs are supported.")

    f_csv = StringIO(string_data)
    reader = csv.reader(f_csv)
    
    # Parse headers/rows
    try:
        rows = list(reader)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV format.")
        
    if not rows:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty")
        
    # Determine columns
    header = rows[0]
    college_idx, branch_idx, notes_idx, cat_idx = -1, -1, -1, -1
    for idx, col in enumerate(header):
        col_clean = col.lower().strip()
        if ("college" in col_clean or "code" in col_clean) and college_idx == -1:
            college_idx = idx
        elif "branch" in col_clean or "course" in col_clean:
            branch_idx = idx
        elif "note" in col_clean:
            notes_idx = idx
        elif "category" in col_clean or "type" in col_clean:
            cat_idx = idx
            
    # Fallback to defaults if headers match simple positional columns [college_code, branch_code]
    if college_idx == -1 or branch_idx == -1:
        college_idx = 0
        branch_idx = 1
        
    extracted_rows = []
    # Skip header
    data_rows = rows[1:] if len(rows) > 1 else rows
    
    for r in data_rows:
        if not r or len(r) <= max(college_idx, branch_idx):
            continue
        college_code = r[college_idx].strip()
        branch_code = r[branch_idx].strip()
        notes = r[notes_idx].strip() if notes_idx != -1 and len(r) > notes_idx else None
        cat = r[cat_idx].strip() if cat_idx != -1 and len(r) > cat_idx else "Moderate"
        extracted_rows.append((college_code, branch_code, notes, cat))

    # O(1) DB roundtrip batch check: query CollegeBranch mappings for all extracted pairs
    valid_choices = []
    if extracted_rows:
        unique_colleges = {row[0] for row in extracted_rows}
        college_branches = db.query(CollegeBranch.college_code, CollegeBranch.branch_code).filter(
            CollegeBranch.college_code.in_(unique_colleges)
        ).all()
        valid_pairs = {(cb[0], cb[1]) for cb in college_branches}

        for college_code, branch_code, notes, cat in extracted_rows:
            if (college_code, branch_code) in valid_pairs:
                valid_choices.append({
                    "college_code": college_code,
                    "branch_code": branch_code,
                    "notes": notes,
                    "category": cat if cat in ["Safe", "Moderate", "Ambitious"] else "Moderate"
                })
            
    if not valid_choices:
        raise HTTPException(status_code=400, detail="No valid college and branch combinations were extracted from the CSV.")
        
    # Check maximum constraints
    count = db.query(UserCollegePreference).filter(UserCollegePreference.workspace_id == ws.id).count()
    if count + len(valid_choices) > 300:
        raise HTTPException(status_code=400, detail=f"Uploading this file would add {len(valid_choices)} items, exceeding the absolute TNEA maximum limit of 300 selections.")
        
    for index, item in enumerate(valid_choices):
        pref = UserCollegePreference(
            workspace_id=ws.id,
            preference_group="primary",
            priority=count + index + 1,
            college_code=item["college_code"],
            branch_code=item["branch_code"],
            category=item["category"],
            notes=item["notes"]
        )
        db.add(pref)
        
    db.commit()
    return {"success": True, "message": f"Successfully parsed and appended {len(valid_choices)} choices to your filing panel."}
