import uuid
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scan import ScanResult
from app.scanners.orchestrator import run_all_scans
from app.ai.explainer import generate_ai_summary

router = APIRouter()


class ScanRequest(BaseModel):
    """Request body for initiating a scan."""
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain")
        return v


class ScanResponse(BaseModel):
    """Response body for scan results."""
    id: str
    url: str
    score: int
    results: dict
    ai_summary: str | None
    created_at: str


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    request: ScanRequest,
    db: AsyncSession = Depends(get_db),
) -> ScanResponse:
    """Run a full security scan on the provided URL."""
    try:
        scan_results = await run_all_scans(request.url)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to scan URL: {str(exc)}",
        )

    ai_summary: str | None = None
    try:
        ai_summary = await generate_ai_summary(request.url, scan_results)
    except Exception:
        ai_summary = "AI summary is temporarily unavailable."

    scan_record = ScanResult(
        url=request.url,
        score=scan_results["score"],
        results=scan_results,
        ai_summary=ai_summary,
    )
    db.add(scan_record)
    await db.flush()
    await db.refresh(scan_record)

    return ScanResponse(
        id=str(scan_record.id),
        url=scan_record.url,
        score=scan_record.score,
        results=scan_record.results,
        ai_summary=scan_record.ai_summary,
        created_at=scan_record.created_at.isoformat(),
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ScanResponse:
    """Retrieve a previously saved scan result by ID."""
    result = await db.execute(
        select(ScanResult).where(ScanResult.id == scan_id)
    )
    scan_record = result.scalar_one_or_none()

    if scan_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with id '{scan_id}' not found",
        )

    return ScanResponse(
        id=str(scan_record.id),
        url=scan_record.url,
        score=scan_record.score,
        results=scan_record.results,
        ai_summary=scan_record.ai_summary,
        created_at=scan_record.created_at.isoformat(),
    )
