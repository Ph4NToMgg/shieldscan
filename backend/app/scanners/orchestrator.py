import asyncio
from typing import Any

from app.scanners.ssl_checker import check_ssl
from app.scanners.headers_checker import check_headers
from app.scanners.redirect_checker import check_redirect


def _calculate_score(
    ssl_result: dict[str, Any],
    header_results: list[dict[str, Any]],
    redirect_result: dict[str, Any],
) -> int:
    """
    Calculate a security score from 0–100 based on scan results.

    Weights:
    - SSL certificate:      30 points
    - Security headers:     50 points (10 per header)
    - HTTP→HTTPS redirect:  20 points
    """
    score = 0

    # SSL: 30 points
    if ssl_result["passed"]:
        if ssl_result["severity"] == "ok":
            score += 30
        elif ssl_result["severity"] == "warning":
            score += 20

    # Headers: 10 points each, 50 total
    for header in header_results:
        if header["passed"]:
            score += 10

    # Redirect: 20 points
    if redirect_result["passed"]:
        score += 20

    return min(score, 100)


async def run_all_scans(url: str) -> dict[str, Any]:
    """
    Run all security scanners concurrently and return
    a combined result dict with individual results and overall score.
    """
    ssl_result, header_results, redirect_result = await asyncio.gather(
        check_ssl(url),
        check_headers(url),
        check_redirect(url),
    )

    score = _calculate_score(ssl_result, header_results, redirect_result)

    total_checks = 1 + len(header_results) + 1  # SSL + headers + redirect
    passed_checks = (
        (1 if ssl_result["passed"] else 0)
        + sum(1 for h in header_results if h["passed"])
        + (1 if redirect_result["passed"] else 0)
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
    }
