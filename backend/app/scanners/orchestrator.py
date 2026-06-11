import asyncio
from typing import Any

from app.scanners.ssl_checker import check_ssl
from app.scanners.headers_checker import check_headers
from app.scanners.redirect_checker import check_redirect
from app.scanners.cookie_checker import check_cookies
from app.scanners.mixed_content_checker import check_mixed_content
from app.scanners.domain_checker import check_domain


def _score_check(result: dict[str, Any], max_points: int) -> int:
    """
    Score a single check result based on passed status and severity.

    - passed + ok:       100% of max_points
    - passed + warning:   60% of max_points (check passed but could be better)
    - failed (any):        0  points (check failed — no credit)
    """
    if not result.get("passed", False):
        return 0

    severity = result.get("severity", "critical")
    if severity == "ok":
        return max_points
    elif severity == "warning":
        return round(max_points * 0.6)
    else:
        return 0

# Weights for individual security headers, based on real-world importance.
# Headers not in this map (e.g. leakage checks) get 0 base weight.
HEADER_WEIGHTS: dict[str, int] = {
    "Content-Security-Policy": 10,       # Critical: XSS protection
    "Strict-Transport-Security": 8,      # Critical: forces HTTPS
    "X-Frame-Options": 5,                # Important: clickjacking protection
    "X-Content-Type-Options": 5,         # Important: MIME sniffing
    "Referrer-Policy": 3,                # Moderate: privacy
    "Permissions-Policy": 2,             # Minor: browser feature control
    "X-Permitted-Cross-Domain-Policies": 2,  # Minor: Flash is dead
}
# Total header weight: 10+8+5+5+3+2+2 = 35
# Total score: SSL(20) + Redirect(15) + Headers(35) + Mixed(15) + Cookies(10) + Domain(5) = 100

LEAKAGE_PENALTY = 3  # Points subtracted per info leakage finding


def _calculate_score(
    ssl_result: dict[str, Any],
    header_results: list[dict[str, Any]],
    redirect_result: dict[str, Any],
    cookie_result: dict[str, Any],
    mixed_content_result: dict[str, Any],
    domain_result: dict[str, Any],
) -> int:
    """
    Calculate a security score from 0–100 based on scan results.

    Uses tiered weights — critical checks are worth more than nice-to-have ones.
    Leakage findings (X-Powered-By, Server version) act as penalties.

    Weights (base total = 100):
    - SSL certificate:          20 points
    - HTTP→HTTPS redirect:      15 points
    - Mixed content:            15 points
    - Security headers:         35 points (tiered per header)
    - Cookie security:          10 points
    - Domain expiry:             5 points
    - Info leakage:             -3 per finding (penalty)
    """
    score = 0

    score += _score_check(ssl_result, 20)
    score += _score_check(redirect_result, 15)
    score += _score_check(mixed_content_result, 15)
    score += _score_check(cookie_result, 10)
    score += _score_check(domain_result, 5)

    for header in header_results:
        header_name = header.get("name", "")
        weight = HEADER_WEIGHTS.get(header_name, 0)

        if weight > 0:
            # Regular security header — score based on weight
            score += _score_check(header, weight)
        elif "(Leakage)" in header_name:
            # Info leakage is a penalty — subtract points
            if not header.get("passed", False):
                score -= LEAKAGE_PENALTY

    return max(0, min(score, 100))


async def run_all_scans(url: str) -> dict[str, Any]:
    """
    Run all security scanners concurrently and return
    a combined result dict with individual results and overall score.
    """
    (
        ssl_result,
        header_results,
        redirect_result,
        cookie_result,
        mixed_content_result,
        domain_result,
    ) = await asyncio.gather(
        check_ssl(url),
        check_headers(url),
        check_redirect(url),
        check_cookies(url),
        check_mixed_content(url),
        check_domain(url),
    )

    score = _calculate_score(
        ssl_result,
        header_results,
        redirect_result,
        cookie_result,
        mixed_content_result,
        domain_result,
    )

    # Count total checks: SSL + headers + redirect + cookies + mixed content + domain
    total_checks = 1 + len(header_results) + 1 + 1 + 1 + 1
    passed_checks = (
        (1 if ssl_result["passed"] else 0)
        + sum(1 for h in header_results if h["passed"])
        + (1 if redirect_result["passed"] else 0)
        + (1 if cookie_result["passed"] else 0)
        + (1 if mixed_content_result["passed"] else 0)
        + (1 if domain_result["passed"] else 0)
    )

    return {
        "url": url,
        "score": score,
        "summary": {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
        },
        "ssl": ssl_result,
        "headers": header_results,
        "redirect": redirect_result,
        "cookies": cookie_result,
        "mixed_content": mixed_content_result,
        "domain": domain_result,
    }
