import httpx
from html.parser import HTMLParser
from urllib.parse import urlparse
from typing import TypedDict, Literal


class MixedContentResult(TypedDict):
    check: str
    passed: bool
    detail: str
    severity: Literal["ok", "warning", "critical"]
    mixed_urls: list[str]


class _MixedContentParser(HTMLParser):
    """Parse HTML and collect HTTP URLs from resource-loading attributes."""

    # Tags and their attributes that load external resources
    RESOURCE_ATTRS: dict[str, list[str]] = {
        "script": ["src"],
        "link": ["href"],
        "img": ["src", "srcset"],
        "iframe": ["src"],
        "video": ["src"],
        "audio": ["src"],
        "source": ["src", "srcset"],
        "object": ["data"],
        "embed": ["src"],
        "form": ["action"],
    }

    def __init__(self) -> None:
        super().__init__()
        self.mixed_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        check_attrs = self.RESOURCE_ATTRS.get(tag.lower())
        if not check_attrs:
            return

        attr_dict = {k.lower(): v for k, v in attrs if v}
        for attr_name in check_attrs:
            value = attr_dict.get(attr_name, "")
            if not value:
                continue

            # Handle srcset (comma-separated list of URLs with optional descriptors)
            if attr_name == "srcset":
                for entry in value.split(","):
                    url_part = entry.strip().split()[0] if entry.strip() else ""
                    if url_part.startswith("http://"):
                        self.mixed_urls.append(url_part)
            elif value.startswith("http://"):
                self.mixed_urls.append(value)


async def check_mixed_content(url: str) -> MixedContentResult:
    """
    Check if an HTTPS page loads any resources over insecure HTTP.
    Mixed content weakens HTTPS security and may be blocked by browsers.
    """
    parsed_url = urlparse(url)

    # Only relevant for HTTPS sites
    if parsed_url.scheme != "https":
        return MixedContentResult(
            check="mixed_content",
            passed=True,
            detail="Site uses HTTP — mixed content check is not applicable.",
            severity="ok",
            mixed_urls=[],
        )

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            verify=True,
        ) as client:
            response = await client.get(url)

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return MixedContentResult(
                check="mixed_content",
                passed=True,
                detail="Response is not HTML — mixed content check is not applicable.",
                severity="ok",
                mixed_urls=[],
            )

        parser = _MixedContentParser()
        parser.feed(response.text)

        # Deduplicate
        mixed_urls = list(dict.fromkeys(parser.mixed_urls))

        if not mixed_urls:
            return MixedContentResult(
                check="mixed_content",
                passed=True,
                detail="No mixed content detected. All resources are loaded over HTTPS.",
                severity="ok",
                mixed_urls=[],
            )

        detail = (
            f"Found {len(mixed_urls)} resource(s) loaded over insecure HTTP. "
            f"Examples: {', '.join(mixed_urls[:3])}"
        )
        if len(mixed_urls) > 3:
            detail += f" ... and {len(mixed_urls) - 3} more."

        return MixedContentResult(
            check="mixed_content",
            passed=False,
            detail=detail,
            severity="critical",
            mixed_urls=mixed_urls[:10],  # Return up to 10 URLs
        )

    except httpx.TimeoutException:
        return MixedContentResult(
            check="mixed_content",
            passed=False,
            detail="Request timed out — could not check for mixed content.",
            severity="critical",
            mixed_urls=[],
        )
    except httpx.RequestError as exc:
        return MixedContentResult(
            check="mixed_content",
            passed=False,
            detail=f"Request failed: {str(exc)} — could not check for mixed content.",
            severity="critical",
            mixed_urls=[],
        )
