import httpx
from typing import TypedDict, Literal


class HeaderCheckResult(TypedDict):
    check: str
    name: str
    passed: bool
    detail: str
    severity: Literal["ok", "warning", "critical"]


SECURITY_HEADERS: dict[str, dict[str, str]] = {
    "Content-Security-Policy": {
        "description": "Controls which resources the browser is allowed to load.",
        "severity_missing": "critical",
    },
    "X-Frame-Options": {
        "description": "Prevents the page from being embedded in iframes (clickjacking protection).",
        "severity_missing": "warning",
    },
    "X-Content-Type-Options": {
        "description": "Prevents MIME-type sniffing attacks.",
        "severity_missing": "warning",
    },
    "Strict-Transport-Security": {
        "description": "Forces browsers to use HTTPS for all future requests.",
        "severity_missing": "critical",
    },
    "Referrer-Policy": {
        "description": "Controls how much referrer information is sent with requests.",
        "severity_missing": "warning",
    },
}


async def check_headers(url: str) -> list[HeaderCheckResult]:
    """
    Check the presence of critical HTTP security headers.
    Returns a list of results, one per header checked.
    """
    results: list[HeaderCheckResult] = []

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            verify=True,
        ) as client:
            response = await client.get(url)

        response_headers = {k.lower(): v for k, v in response.headers.items()}

        for header_name, header_info in SECURITY_HEADERS.items():
            header_key = header_name.lower()
            header_value = response_headers.get(header_key)

            if header_value:
                results.append(
                    HeaderCheckResult(
                        check="security_header",
                        name=header_name,
                        passed=True,
                        detail=f"{header_name} is set: {header_value}",
                        severity="ok",
                    )
                )
            else:
                severity = header_info["severity_missing"]
                results.append(
                    HeaderCheckResult(
                        check="security_header",
                        name=header_name,
                        passed=False,
                        detail=f"{header_name} header is missing. {header_info['description']}",
                        severity=severity,
                    )
                )

    except httpx.TimeoutException:
        for header_name in SECURITY_HEADERS:
            results.append(
                HeaderCheckResult(
                    check="security_header",
                    name=header_name,
                    passed=False,
                    detail=f"Request timed out — could not check {header_name}.",
                    severity="critical",
                )
            )
    except httpx.RequestError as exc:
        for header_name in SECURITY_HEADERS:
            results.append(
                HeaderCheckResult(
                    check="security_header",
                    name=header_name,
                    passed=False,
                    detail=f"Request failed: {str(exc)} — could not check {header_name}.",
                    severity="critical",
                )
            )

    return results
