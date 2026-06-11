import httpx
from urllib.parse import urlparse
from typing import TypedDict, Literal


class RedirectCheckResult(TypedDict):
    check: str
    passed: bool
    detail: str
    severity: Literal["ok", "warning", "critical"]


async def check_redirect(url: str) -> RedirectCheckResult:
    """
    Check if HTTP version of the URL redirects to HTTPS.
    If the URL is already HTTP, test it directly.
    If it's HTTPS, construct the HTTP version and check.
    """
    parsed = urlparse(url)
    http_url = f"http://{parsed.netloc}{parsed.path or '/'}"

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=15.0,
            verify=False,
        ) as client:
            response = await client.get(http_url)

        if response.status_code in (301, 302, 307, 308):
            location = response.headers.get("location", "")
            if location.startswith("https://"):
                return RedirectCheckResult(
                    check="http_to_https_redirect",
                    passed=True,
                    detail=f"HTTP correctly redirects to HTTPS ({response.status_code} → {location}).",
                    severity="ok",
                )
            else:
                return RedirectCheckResult(
                    check="http_to_https_redirect",
                    passed=False,
                    detail=f"HTTP redirects but not to HTTPS. Location: {location}",
                    severity="warning",
                )
        elif response.status_code == 200:
            return RedirectCheckResult(
                check="http_to_https_redirect",
                passed=False,
                detail="HTTP serves content without redirecting to HTTPS. The site is accessible over an insecure connection.",
                severity="critical",
            )
        else:
            return RedirectCheckResult(
                check="http_to_https_redirect",
                passed=False,
                detail=f"HTTP returned unexpected status code {response.status_code}.",
                severity="warning",
            )

    except httpx.TimeoutException:
        return RedirectCheckResult(
            check="http_to_https_redirect",
            passed=False,
            detail="Connection timed out when checking HTTP redirect. Site may not redirect to HTTPS.",
            severity="critical",
        )
    except httpx.RequestError as exc:
        return RedirectCheckResult(
            check="http_to_https_redirect",
            passed=False,
            detail=f"Could not connect via HTTP: {str(exc)}",
            severity="critical",
        )
