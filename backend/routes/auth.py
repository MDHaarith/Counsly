import httpx
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from backend.database import get_db
from backend.models import User, Workspace, WorkspaceSettings, WorkspaceActivity, DeviceFingerprint
from backend.schemas import SessionRequest, UserProfile
from backend.config import settings
from backend.routes.rate_limiter import rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    google_email: EmailStr
    name: str
    google_id: Optional[str] = None
    google_id_token: Optional[str] = None
    device_fingerprint_hash: Optional[str] = None

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def verify_google_identity_token(google_id_token: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": google_id_token},
            )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google identity verification failed.",
        ) from exc

    if payload.get("email_verified") not in {True, "true"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified.",
        )

    if settings.GOOGLE_CLIENT_ID and payload.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google identity token audience mismatch.",
        )

    return payload


def normalize_session_identity(req: SessionRequest, verified_payload: dict | None) -> tuple[str, str, str | None]:
    if verified_payload:
        return (
            verified_payload.get("email") or req.google_email,
            verified_payload.get("name") or req.name,
            verified_payload.get("sub") or req.google_id,
        )
    return req.google_email, req.name, req.google_id

async def get_current_user(request: Request, authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    email = None
    user = None

    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    return user
        except Exception:
            pass  # JWT decode failure — token invalid or expired, proceed unauthenticated

    if settings.ALLOW_DEV_AUTH_FALLBACK:
        if not user:
            email = request.query_params.get("google_email")
            if email:
                user = db.query(User).filter(User.google_email == email).first()

        if not user:
            try:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    body_bytes = await request.body()
                    if body_bytes:
                        import json
                        body_json = json.loads(body_bytes)
                        email = body_json.get("google_email")
                        if email:
                            user = db.query(User).filter(User.google_email == email).first()
            except Exception:
                pass  # Request body JSON parse failure — non-JSON request, proceed with empty body

        if not user and email:
            user_id = str(uuid.uuid4())
            user = User(
                id=user_id,
                auth_user_id=str(uuid.uuid4()),
                google_id=str(uuid.uuid4()),
                google_email=email,
                name=email.split("@")[0].title(),
                created_at=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc)
            )
            db.add(user)
            db.flush()

            workspace_id = str(uuid.uuid4())
            workspace = Workspace(
                id=workspace_id,
                user_id=user.id,
                name=f"{user.name}'s Workspace",
                slug=f"ws-{user_id[:8]}",
                onboarding_step="completed",
                onboarding_completed=True,
                onboarding_completed_at=datetime.now(timezone.utc)
            )
            db.add(workspace)
            db.flush()

            settings_id = str(uuid.uuid4())
            w_settings = WorkspaceSettings(
                id=settings_id,
                workspace_id=workspace_id,
                compact_view=False,
                mobile_density="default",
                theme_mode="mild"
            )
            db.add(w_settings)

            activity = WorkspaceActivity(
                workspace_id=workspace_id,
                event_type="environment_initialized",
                summary="strictly private personal data environment initialized successfully.",
                created_at=datetime.now(timezone.utc)
            )
            db.add(activity)
            db.commit()
            db.refresh(user)
            return user

        if user:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
    )

@router.post("/session", dependencies=[Depends(rate_limit(5, 60))])
async def start_session(req: SessionRequest, db: Session = Depends(get_db)):
    verified_payload = None
    if req.google_id_token:
        verified_payload = await verify_google_identity_token(req.google_id_token)
    elif settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google identity token is required in production.",
        )

    resolved_email, resolved_name, resolved_google_id = normalize_session_identity(req, verified_payload)

    user = db.query(User).filter(User.google_email == resolved_email).first()
    is_new = False

    if not user:
        is_new = True
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            auth_user_id=str(uuid.uuid4()),
            google_id=resolved_google_id or str(uuid.uuid4()),
            google_email=resolved_email,
            name=resolved_name,
            device_fingerprint_hash=req.device_fingerprint_hash,
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc)
        )
        db.add(user)
        db.flush()  # Lock user ID to resolve constraints
        
        # Initializestrictly private personal data environment (Workspace)
        workspace_id = str(uuid.uuid4())
        workspace = Workspace(
            id=workspace_id,
            user_id=user.id,
            name=f"{resolved_name}'s Workspace",
            slug=f"ws-{user_id[:8]}",
            onboarding_step="marks"
        )
        db.add(workspace)
        db.flush()
        
        # Initialize workspace settings
        settings_id = str(uuid.uuid4())
        w_settings = WorkspaceSettings(
            id=settings_id,
            workspace_id=workspace_id,
            compact_view=False,
            mobile_density="default",
            theme_mode="mild"
        )
        db.add(w_settings)
        
        # Log initialization activity
        activity = WorkspaceActivity(
            workspace_id=workspace_id,
            event_type="environment_initialized",
            summary="strictly private personal data environment initialized successfully.",
            created_at=datetime.now(timezone.utc)
        )
        db.add(activity)
    else:
        # Check device fingerprint block
        if req.device_fingerprint_hash and user.device_fingerprint_hash:
            if user.device_fingerprint_hash != req.device_fingerprint_hash:
                # Check how many accounts use this fingerprint to prevent sharing abuse
                existing_fingerprints = db.query(DeviceFingerprint).filter(
                    DeviceFingerprint.fingerprint_hash == req.device_fingerprint_hash
                ).all()
                if len(existing_fingerprints) >= 3:
                    raise HTTPException(
                        status_code=403,
                        detail="Device fingerprint limit exceeded. Account sharing is strictly restricted."
                    )
        
        user.last_login = datetime.now(timezone.utc)
        if req.device_fingerprint_hash and not user.device_fingerprint_hash:
            user.device_fingerprint_hash = req.device_fingerprint_hash
            
    # Record current fingerprint to ledger
    if req.device_fingerprint_hash:
        fp_exists = db.query(DeviceFingerprint).filter(
            DeviceFingerprint.fingerprint_hash == req.device_fingerprint_hash,
            DeviceFingerprint.user_id == user.id
        ).first()
        if not fp_exists:
            db.add(DeviceFingerprint(
                fingerprint_hash=req.device_fingerprint_hash,
                user_id=user.id
            ))
            
    db.commit()
    db.refresh(user)
    
    # 2. Generate Access Token
    token = create_access_token({"sub": user.id, "email": user.google_email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "profile": {
            "id": user.id,
            "name": user.name,
            "google_email": user.google_email,
            "welcome_message_sent": user.welcome_message_sent,
            "roll_number": user.roll_number,
            "roll_number_verified": user.roll_number_verified,
            "workspace_onboarding_step": user.workspace.onboarding_step if user.workspace else "marks"
        }
    }

@router.get("/profile", response_model=UserProfile)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/register", dependencies=[Depends(rate_limit(5, 60))])
async def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    verified_payload = None
    if req.google_id_token:
        verified_payload = await verify_google_identity_token(req.google_id_token)
    elif settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google identity token is required in production.",
        )

    resolved_email = verified_payload.get("email") if verified_payload else req.google_email
    resolved_name = verified_payload.get("name") if verified_payload else req.name
    resolved_google_id = verified_payload.get("sub") if verified_payload else req.google_id

    user = db.query(User).filter(User.google_email == resolved_email).first()

    if not user:
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            auth_user_id=str(uuid.uuid4()),
            google_id=resolved_google_id or str(uuid.uuid4()),
            google_email=resolved_email,
            name=resolved_name,
            device_fingerprint_hash=req.device_fingerprint_hash,
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc)
        )
        db.add(user)
        db.flush()
        
        # Initialize personal data environment (Workspace)
        workspace_id = str(uuid.uuid4())
        workspace = Workspace(
            id=workspace_id,
            user_id=user.id,
            name=f"{resolved_name}'s Workspace",
            slug=f"ws-{user_id[:8]}",
            onboarding_step="completed",
            onboarding_completed=True,
            onboarding_completed_at=datetime.now(timezone.utc)
        )
        db.add(workspace)
        db.flush()
        
        # Initialize workspace settings
        settings_id = str(uuid.uuid4())
        w_settings = WorkspaceSettings(
            id=settings_id,
            workspace_id=workspace_id,
            compact_view=False,
            mobile_density="default",
            theme_mode="mild"
        )
        db.add(w_settings)
        
        # Log activity
        activity = WorkspaceActivity(
            workspace_id=workspace_id,
            event_type="environment_initialized",
            summary="strictly private personal data environment initialized successfully.",
            created_at=datetime.now(timezone.utc)
        )
        db.add(activity)
    else:
        user.last_login = datetime.now(timezone.utc)
        if req.device_fingerprint_hash and not user.device_fingerprint_hash:
            user.device_fingerprint_hash = req.device_fingerprint_hash
            
        if user.workspace:
            user.workspace.onboarding_step = "completed"
            user.workspace.onboarding_completed = True
            user.workspace.onboarding_completed_at = datetime.now(timezone.utc)
        else:
            workspace_id = str(uuid.uuid4())
            workspace = Workspace(
                id=workspace_id,
                user_id=user.id,
                name=f"{user.name}'s Workspace",
                slug=f"ws-{user.id[:8]}",
                onboarding_step="completed",
                onboarding_completed=True,
                onboarding_completed_at=datetime.now(timezone.utc)
            )
            db.add(workspace)
            db.flush()
            
            settings_id = str(uuid.uuid4())
            w_settings = WorkspaceSettings(
                id=settings_id,
                workspace_id=workspace_id,
                compact_view=False,
                mobile_density="default",
                theme_mode="mild"
            )
            db.add(w_settings)
            
    db.commit()
    db.refresh(user)
    
    # Generate token
    token = create_access_token({"sub": user.id, "email": user.google_email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "profile": {
            "id": user.id,
            "name": user.name,
            "google_email": user.google_email,
            "welcome_message_sent": user.welcome_message_sent,
            "roll_number": user.roll_number,
            "roll_number_verified": user.roll_number_verified,
            "workspace_onboarding_step": user.workspace.onboarding_step if user.workspace else "completed"
        }
    }
