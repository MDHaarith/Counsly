from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ScrapingJob
from backend.schemas import ScrapingJobRequest, ScrapingJobResponse
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/scraping", tags=["scraping"])


def build_scraping_job_status(dataset: str, source_url: str | None, status: str, row_count: int, error_message: str | None = None) -> dict:
    return {
        "dataset": dataset,
        "source_url": source_url,
        "job_type": "real_time_scraping",
        "status": status,
        "row_count": row_count,
        "error_message": error_message,
    }


def default_scraping_jobs() -> list[ScrapingJobResponse]:
    return [
        ScrapingJobResponse(**build_scraping_job_status("cutoff_data", "official cutoff source", "ready", 0)),
        ScrapingJobResponse(**build_scraping_job_status("seat_matrix", "official seat matrix source", "ready", 0)),
        ScrapingJobResponse(**build_scraping_job_status("rank_list", "official rank list source", "ready", 0)),
    ]


@router.get("/jobs", response_model=list[ScrapingJobResponse])
def get_scraping_jobs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    jobs = db.query(ScrapingJob).order_by(ScrapingJob.created_at.desc()).limit(12).all()
    if not jobs:
        return default_scraping_jobs()
    return [
        ScrapingJobResponse(
            dataset=job.dataset,
            source_url=job.source_url,
            job_type=job.job_type,
            status=job.status,
            row_count=job.row_count,
            error_message=job.error_message,
        )
        for job in jobs
    ]


@router.post("/jobs", response_model=ScrapingJobResponse)
def create_scraping_job(req: ScrapingJobRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    payload = build_scraping_job_status(req.dataset, req.source_url, req.status, req.row_count, req.error_message)
    record = ScrapingJob(**payload)
    db.add(record)
    db.commit()
    return ScrapingJobResponse(**payload)
