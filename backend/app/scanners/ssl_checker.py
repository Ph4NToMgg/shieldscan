import ssl
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import TypedDict, Literal


class SSLCheckResult(TypedDict):
    check: str
    passed: bool
    detail: str
    severity: Literal["ok", "warning", "critical"]


async def check_ssl(url: str) -> SSLCheckResult:
    """
    Check the SSL certificate of the given URL.
    Verifies validity and warns if expiring within 30 days.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or parsed.netloc

    if not hostname:
        return SSLCheckResult(
            check="ssl_certificate",
            passed=False,
            detail="Could not parse hostname from URL.",
            severity="critical",
        )

    try:
        context = ssl.create_default_context()
        conn = context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=hostname,
        )
        conn.settimeout(10)
        conn.connect((hostname, 443))
        cert = conn.getpeercert()
        conn.close()

        if cert is None:
            return SSLCheckResult(
                check="ssl_certificate",
                passed=False,
                detail="No SSL certificate found on the server.",
                severity="critical",
            )

        not_after_str = cert.get("notAfter", "")
        not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc
        )
        days_remaining = (not_after - datetime.now(timezone.utc)).days

        if days_remaining < 0:
            return SSLCheckResult(
                check="ssl_certificate",
                passed=False,
                detail=f"SSL certificate expired {abs(days_remaining)} days ago.",
                severity="critical",
            )

        if days_remaining < 30:
            return SSLCheckResult(
                check="ssl_certificate",
                passed=True,
                detail=f"SSL certificate is valid but expires in {days_remaining} days. Consider renewing soon.",
                severity="warning",
            )

        issuer_parts = cert.get("issuer", ())
        issuer_name = "Unknown"
        for rdn in issuer_parts:
            for attr_type, attr_value in rdn:
                if attr_type == "organizationName":
                    issuer_name = attr_value
                    break

        return SSLCheckResult(
            check="ssl_certificate",
            passed=True,
            detail=f"SSL certificate is valid. Issued by {issuer_name}, expires in {days_remaining} days.",
            severity="ok",
        )

    except ssl.SSLCertVerificationError as exc:
        return SSLCheckResult(
            check="ssl_certificate",
            passed=False,
            detail=f"SSL certificate verification failed: {str(exc)}",
            severity="critical",
        )
    except socket.timeout:
        return SSLCheckResult(
            check="ssl_certificate",
            passed=False,
            detail="Connection timed out while checking SSL certificate.",
            severity="critical",
        )
    except socket.gaierror:
        return SSLCheckResult(
            check="ssl_certificate",
            passed=False,
            detail=f"Could not resolve hostname: {hostname}",
            severity="critical",
        )
    except Exception as exc:
        return SSLCheckResult(
            check="ssl_certificate",
            passed=False,
            detail=f"SSL check failed: {str(exc)}",
            severity="critical",
        )
