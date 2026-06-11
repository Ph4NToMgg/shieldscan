import httpx
from typing import TypedDict, Literal


class CookieCheckResult(TypedDict):
    check: str
    passed: bool
    detail: str
    severity: Literal["ok", "warning", "critical"]
    cookies_analyzed: int


async def check_cookies(url: str) -> CookieCheckResult:
    """
    Check Set-Cookie headers for security flags:
    - Secure: cookie only sent over HTTPS
    - HttpOnly: cookie inaccessible to JavaScript
    - SameSite: protection against CSRF attacks
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            verify=True,
        ) as client:
            response = await client.get(url)

        raw_cookies = response.headers.get_list("set-cookie")

        if not raw_cookies:
            return CookieCheckResult(
                check="cookie_security",
                passed=True,
                detail="No cookies are set by this page. No cookie security issues detected.",
                severity="ok",
                cookies_analyzed=0,
            )

        issues: list[str] = []
        total_cookies = len(raw_cookies)

        for cookie_str in raw_cookies:
            cookie_lower = cookie_str.lower()
            # Extract cookie name (everything before the first '=')
            cookie_name = cookie_str.split("=", 1)[0].strip()

            missing_flags: list[str] = []
            if "secure" not in cookie_lower:
                missing_flags.append("Secure")
            if "httponly" not in cookie_lower:
                missing_flags.append("HttpOnly")
            if "samesite" not in cookie_lower:
                missing_flags.append("SameSite")

            if missing_flags:
                issues.append(f"Cookie '{cookie_name}' is missing: {', '.join(missing_flags)}")

        if not issues:
            return CookieCheckResult(
                check="cookie_security",
                passed=True,
                detail=f"All {total_cookies} cookie(s) have Secure, HttpOnly, and SameSite flags set.",
                severity="ok",
                cookies_analyzed=total_cookies,
            )

        detail = f"{len(issues)} of {total_cookies} cookie(s) have missing security flags. " + " | ".join(issues[:3])
        if len(issues) > 3:
            detail += f" ... and {len(issues) - 3} more."

        return CookieCheckResult(
            check="cookie_security",
            passed=False,
            detail=detail,
            severity="warning",
            cookies_analyzed=total_cookies,
        )

    except httpx.TimeoutException:
        return CookieCheckResult(
            check="cookie_security",
            passed=False,
            detail="Request timed out — could not check cookie security.",
            severity="critical",
            cookies_analyzed=0,
        )
    except httpx.RequestError as exc:
        return CookieCheckResult(
            check="cookie_security",
            passed=False,
            detail=f"Request failed: {str(exc)} — could not check cookie security.",
            severity="critical",
            cookies_analyzed=0,
        )
