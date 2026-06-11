import asyncio
from typing import Any

from app.scanners.ssl_checker import check_ssl
from app.scanners.headers_checker import check_headers
from app.scanners.redirect_checker import check_redirect
from app.scanners.cookie_checker import check_cookies
from app.scanners.mixed_content_checker import check_mixed_content
from app.scanners.domain_checker import check_domain


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

    Weights (total = 100):
    - SSL certificate:          25 points
    - HTTP→HTTPS redirect:      15 points
    - Security headers:          5 points each (7 headers = 35 points)
    - Cookie security:          10 points
    - Mixed content:            10 points
    - Domain expiry:             5 points
    """
    score = 0

    # SSL: 25 points
    if ssl_result["passed"]:
        if ssl_result["severity"] == "ok":
            score += 25
        elif ssl_result["severity"] == "warning":
            score += 17

    # Redirect: 15 points
    if redirect_result["passed"]:
        score += 15

    # Headers: 5 points each
    for header in header_results:
        if header["passed"]:
            score += 5

    # Cookies: 10 points
    if cookie_result["passed"]:
        score += 10

    # Mixed content: 10 points
    if mixed_content_result["passed"]:
        score += 10

    # Domain expiry: 5 points
    if domain_result["passed"]:
        score += 5

    return min(score, 100)


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
