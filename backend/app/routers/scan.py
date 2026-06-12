import ipaddress
import uuid
from typing import Optional
from urllib.parse import urlparse

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scan import ScanResult
from app.models.user_credits import UserCredits
from app.scanners.orchestrator import run_all_scans
from app.ai.explainer import generate_ai_summary
from app.limiter import limiter
from app.auth import require_auth

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

        hostname = parsed.hostname or ""

        # Block localhost
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            raise ValueError("Scanning localhost is not allowed")

        # Block internal hostnames with no dots (e.g. http://internalserver/)
        if "." not in hostname:
            raise ValueError("Internal hostnames are not allowed")

        # Block private IP ranges
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise ValueError("Scanning private IP addresses is not allowed")
        except ValueError as e:
            if "not allowed" in str(e):
                raise
            pass  # hostname is a domain name, not an IP — that's fine

        return v


class ScanResponse(BaseModel):
    """Response body for scan results."""
    id: str
    url: str
    score: int
    results: dict
    ai_summary: Optional[str] = None
    user_id: Optional[str] = None
    created_at: str
    credits_remaining: Optional[int] = None


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_scan(
    request: Request,
    scan_request: ScanRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
) -> ScanResponse:
    """Run a full security scan on the provided URL. Requires authentication."""

    # --- Credit check: get or create user credits row ---
    result = await db.execute(
        select(UserCredits).where(UserCredits.user_id == user_id)
    )
    user_credits = result.scalar_one_or_none()

    if user_credits is None:
        # First-time user: create credits row with 3 free credits
        user_credits = UserCredits(user_id=user_id)
        db.add(user_credits)
        await db.flush()

    if user_credits.credits_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No scan credits remaining. Purchase more credits to continue.",
        )

    # Decrement credits
    user_credits.credits_remaining -= 1

    # --- Run scan ---
    try:
        scan_results = await run_all_scans(scan_request.url)
    except Exception as exc:
        # Refund the credit on scan failure
        user_credits.credits_remaining += 1
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to scan URL: {str(exc)}",
        )

    ai_summary: Optional[str] = None
    try:
        ai_summary = await generate_ai_summary(scan_request.url, scan_results)
    except Exception:
        ai_summary = "AI summary is temporarily unavailable."

    scan_record = ScanResult(
        url=scan_request.url,
        score=scan_results["score"],
        results=scan_results,
        ai_summary=ai_summary,
        user_id=user_id,
    )
    db.add(scan_record)
    await db.commit()
    await db.refresh(scan_record)

    return ScanResponse(
        id=str(scan_record.id),
        url=scan_record.url,
        score=scan_record.score,
        results=scan_record.results,
        ai_summary=scan_record.ai_summary,
        user_id=scan_record.user_id,
        created_at=scan_record.created_at.isoformat(),
        credits_remaining=user_credits.credits_remaining,
    )


@router.get("/history")
async def get_scan_history(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
) -> list:
    """Return the authenticated user's scan history, newest first (max 50)."""
    result = await db.execute(
        select(ScanResult)
        .where(ScanResult.user_id == user_id)
        .order_by(ScanResult.created_at.desc())
        .limit(50)
    )
    scans = result.scalars().all()
    return [scan.to_dict() for scan in scans]


@router.get("/credits")
async def get_credits(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
) -> dict:
    """Return the authenticated user's credit balance."""
    result = await db.execute(
        select(UserCredits).where(UserCredits.user_id == user_id)
    )
    user_credits = result.scalar_one_or_none()

    if user_credits is None:
        # First-time user: create credits row with defaults
        user_credits = UserCredits(user_id=user_id)
        db.add(user_credits)
        await db.commit()

    return {
        "credits_remaining": user_credits.credits_remaining,
        "credits_total": user_credits.credits_total,
    }


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the total number of scans performed."""
    try:
        result = await db.execute(select(func.count()).select_from(ScanResult))
        total = result.scalar_one_or_none() or 0
        return {"total_scans": total}
    except Exception:
        return {"total_scans": 0}


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
        user_id=scan_record.user_id,
        created_at=scan_record.created_at.isoformat(),
    )
