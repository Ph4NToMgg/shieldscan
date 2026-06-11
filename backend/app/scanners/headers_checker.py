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
    "Permissions-Policy": {
        "description": "Controls which browser features (camera, microphone, geolocation) the page can use.",
        "severity_missing": "warning",
    },
    "X-Permitted-Cross-Domain-Policies": {
        "description": "Restricts Adobe Flash and PDF cross-domain data loading.",
        "severity_missing": "warning",
    },
}


def _check_header_quality(header_name: str, header_value: str) -> str | None:
    """
    Analyze the quality of specific security headers.
    Returns a description of the issue, or None if the header is well-configured.
    """
    issues: list[str] = []
    value_lower = header_value.lower()

    if header_name == "Content-Security-Policy":
        # Parse CSP into directives
        directives: dict[str, str] = {}
        for part in value_lower.split(";"):
            part = part.strip()
            if part:
                tokens = part.split(None, 1)
                if tokens:
                    directives[tokens[0]] = tokens[1] if len(tokens) > 1 else ""

        # Only flag unsafe-inline/unsafe-eval in script-src or default-src
        # Having them in style-src is common and acceptable
        script_scope = directives.get("script-src", "") + " " + directives.get("default-src", "")

        if "'unsafe-inline'" in script_scope:
            issues.append("script-src contains 'unsafe-inline' which allows inline scripts (XSS risk)")
        if "'unsafe-eval'" in script_scope:
            issues.append("script-src contains 'unsafe-eval' which allows eval() (XSS risk)")
        if "default-src *" in value_lower or "script-src *" in value_lower:
            issues.append("uses wildcard (*) source which defeats the purpose of CSP")

    elif header_name == "Strict-Transport-Security":
        if "includesubdomains" not in value_lower:
            issues.append("missing 'includeSubDomains' directive")
        # Check max-age value
        import re
        max_age_match = re.search(r"max-age=(\d+)", value_lower)
        if max_age_match:
            max_age = int(max_age_match.group(1))
            if max_age < 15768000:  # Less than 6 months
                issues.append(f"max-age is {max_age}s (less than recommended 6 months)")

    elif header_name == "X-Frame-Options":
        valid_values = ("deny", "sameorigin")
        if value_lower.strip() not in valid_values:
            issues.append(f"unexpected value '{header_value}' (should be DENY or SAMEORIGIN)")

    return "; ".join(issues) if issues else None


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
                # Check header quality for specific headers
                quality_issue = _check_header_quality(header_name, header_value)
                if quality_issue:
                    results.append(
                        HeaderCheckResult(
                            check="security_header",
                            name=header_name,
                            passed=True,
                            detail=f"{header_name} is set but has issues: {quality_issue}. Value: {header_value}",
                            severity="warning",
                        )
                    )
                else:
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

        # Check for information leakage headers
        _LEAKAGE_HEADERS = {
            "x-powered-by": "X-Powered-By",
            "server": "Server",
        }
        for header_key, display_name in _LEAKAGE_HEADERS.items():
            header_value = response_headers.get(header_key)
            if header_value:
                # "Server: nginx" alone is acceptable; detailed versions are not
                import re
                has_version = bool(re.search(r"\d+\.\d+", header_value))
                if has_version:
                    results.append(
                        HeaderCheckResult(
                            check="security_header",
                            name=f"{display_name} (Leakage)",
                            passed=False,
                            detail=f"{display_name} header exposes server technology: '{header_value}'. This helps attackers find known vulnerabilities for this version.",
                            severity="warning",
                        )
                    )
                elif header_key == "x-powered-by":
                    # X-Powered-By should ideally be removed entirely
                    results.append(
                        HeaderCheckResult(
                            check="security_header",
                            name=f"{display_name} (Leakage)",
                            passed=False,
                            detail=f"{display_name} header is present: '{header_value}'. Consider removing it to reduce information exposure.",
                            severity="warning",
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
