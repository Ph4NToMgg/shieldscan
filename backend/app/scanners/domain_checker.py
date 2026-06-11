import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import TypedDict, Literal


class DomainCheckResult(TypedDict):
    check: str
    passed: bool
    detail: str
    severity: Literal["ok", "warning", "critical"]


async def check_domain(url: str) -> DomainCheckResult:
    """
    Check domain WHOIS data for expiration date.
    - Expired or < 30 days remaining: critical
    - < 90 days remaining: warning
    - >= 90 days remaining: ok
    - WHOIS unavailable: warning (non-blocking)
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    if not hostname:
        return DomainCheckResult(
            check="domain_expiry",
            passed=False,
            detail="Could not parse hostname from URL.",
            severity="critical",
        )

    try:
        # Run whois lookup in a thread to avoid blocking the event loop
        import whois  # type: ignore[import-untyped]

        loop = asyncio.get_event_loop()
        domain_info = await loop.run_in_executor(None, whois.whois, hostname)

        expiration_date = domain_info.expiration_date

        if expiration_date is None:
            return DomainCheckResult(
                check="domain_expiry",
                passed=True,
                detail=f"WHOIS data for '{hostname}' does not include an expiration date. Domain may have lifetime registration.",
                severity="warning",
            )

        # Some domains return a list of expiration dates
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]

        # Ensure timezone-aware comparison
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        days_remaining = (expiration_date - now).days

        if days_remaining < 0:
            return DomainCheckResult(
                check="domain_expiry",
                passed=False,
                detail=f"Domain '{hostname}' expired {abs(days_remaining)} days ago!",
                severity="critical",
            )

        if days_remaining < 30:
            return DomainCheckResult(
                check="domain_expiry",
                passed=False,
                detail=f"Domain '{hostname}' expires in {days_remaining} days! Renew immediately.",
                severity="critical",
            )

        if days_remaining < 90:
            return DomainCheckResult(
                check="domain_expiry",
                passed=True,
                detail=f"Domain '{hostname}' expires in {days_remaining} days. Consider renewing soon.",
                severity="warning",
            )

        formatted_date = expiration_date.strftime("%Y-%m-%d")
        return DomainCheckResult(
            check="domain_expiry",
            passed=True,
            detail=f"Domain '{hostname}' is registered until {formatted_date} ({days_remaining} days remaining).",
            severity="ok",
        )

    except ImportError:
        return DomainCheckResult(
            check="domain_expiry",
            passed=True,
            detail="WHOIS lookup is not available (python-whois not installed). Skipping domain expiry check.",
            severity="warning",
        )
    except Exception as exc:
        return DomainCheckResult(
            check="domain_expiry",
            passed=True,
            detail=f"Could not retrieve WHOIS data for '{hostname}': {str(exc)}. This may be normal for some TLDs.",
            severity="warning",
        )
