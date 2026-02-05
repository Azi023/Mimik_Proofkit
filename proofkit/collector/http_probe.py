"""HTTP-level probing for headers, SSL, redirects, and security."""

import ssl
import socket
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx

from proofkit.utils.logger import logger
from proofkit.utils.exceptions import HttpProbeError

from .models import HttpProbeData, SecurityHeaders, SSLInfo


class HttpProbeCollector:
    """HTTP-level probing for headers, SSL, redirects, and security."""

    # Security headers to check
    SECURITY_HEADERS = [
        "strict-transport-security",
        "content-security-policy",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
        "x-xss-protection",
        "cross-origin-opener-policy",
        "cross-origin-resource-policy",
    ]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def collect(self, url: str) -> HttpProbeData:
        """
        Probe URL for HTTP-level information.

        Args:
            url: Target URL to probe

        Returns:
            HttpProbeData with all collected information
        """
        logger.info(f"Probing HTTP info for {url}")

        # Track redirects
        redirect_chain = self._follow_redirects(url)

        # Main request
        try:
            with httpx.Client(follow_redirects=True, timeout=self.timeout) as client:
                response = client.get(url)

                final_url = str(response.url)
                status_code = response.status_code
                response_time_ms = response.elapsed.total_seconds() * 1000
                headers = dict(response.headers)

        except httpx.TimeoutException:
            raise HttpProbeError(f"Request timed out: {url}")
        except httpx.RequestError as e:
            raise HttpProbeError(f"Request failed: {e}")

        # Check security headers
        security_headers = self._check_security_headers(headers)

        # Check SSL
        ssl_info = self._check_ssl(url)

        # Check robots.txt and sitemap
        robots_txt = self._fetch_robots(url)
        sitemap_exists, sitemap_url = self._check_sitemap(url)

        return HttpProbeData(
            url=url,
            final_url=final_url,
            status_code=status_code,
            redirect_chain=redirect_chain,
            redirect_count=len(redirect_chain) - 1 if redirect_chain else 0,
            response_time_ms=round(response_time_ms, 2),
            headers=headers,
            security_headers=security_headers,
            ssl_info=ssl_info,
            server=headers.get("server"),
            robots_txt=robots_txt,
            sitemap_exists=sitemap_exists,
            sitemap_url=sitemap_url,
        )

    def _follow_redirects(self, url: str, max_redirects: int = 10) -> List[str]:
        """Track redirect chain."""
        chain = []
        current_url = url

        with httpx.Client(follow_redirects=False, timeout=10) as client:
            for _ in range(max_redirects):
                try:
                    response = client.head(current_url, follow_redirects=False)
                    chain.append(current_url)

                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location", "")
                        if not location:
                            break

                        # Handle relative URLs
                        if not location.startswith("http"):
                            parsed = urlparse(current_url)
                            if location.startswith("/"):
                                location = f"{parsed.scheme}://{parsed.netloc}{location}"
                            else:
                                location = f"{parsed.scheme}://{parsed.netloc}/{location}"

                        current_url = location
                    else:
                        break

                except Exception as e:
                    logger.warning(f"Redirect check failed: {e}")
                    break

        return chain

    def _check_security_headers(self, headers: Dict[str, str]) -> SecurityHeaders:
        """Check presence and values of security headers."""
        # Normalize header names to lowercase
        normalized_headers = {k.lower(): v for k, v in headers.items()}

        present = {}
        missing = []

        for header in self.SECURITY_HEADERS:
            value = normalized_headers.get(header)
            if value:
                present[header] = value
            else:
                missing.append(header)

        # Calculate score
        score = (len(present) / len(self.SECURITY_HEADERS)) * 100

        return SecurityHeaders(
            present=present,
            missing=missing,
            has_hsts="strict-transport-security" in present,
            has_csp="content-security-policy" in present,
            has_xframe="x-frame-options" in present,
            score=round(score, 1),
        )

    def _check_ssl(self, url: str) -> Optional[SSLInfo]:
        """Check SSL certificate information."""
        if not url.startswith("https"):
            return SSLInfo(valid=False, error="Not using HTTPS")

        try:
            parsed = urlparse(url)
            hostname = parsed.netloc

            # Remove port if present
            if ":" in hostname:
                hostname = hostname.split(":")[0]

            # Create SSL context
            context = ssl.create_default_context()

            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    if not cert:
                        return SSLInfo(valid=False, error="No certificate returned")

                    # Extract issuer
                    issuer_dict = dict(x[0] for x in cert.get("issuer", []))
                    issuer = issuer_dict.get("organizationName", "Unknown")

                    # Extract subject
                    subject_dict = dict(x[0] for x in cert.get("subject", []))
                    subject = subject_dict.get("commonName", hostname)

                    # Get expiry
                    expires = cert.get("notAfter")
                    days_until_expiry = None

                    if expires:
                        try:
                            expiry_date = datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z")
                            days_until_expiry = (expiry_date - datetime.utcnow()).days
                        except Exception:
                            pass

                    return SSLInfo(
                        valid=True,
                        issuer=issuer,
                        expires=expires,
                        subject=subject,
                        days_until_expiry=days_until_expiry,
                    )

        except ssl.SSLCertVerificationError as e:
            return SSLInfo(valid=False, error=f"Certificate verification failed: {e}")
        except socket.timeout:
            return SSLInfo(valid=False, error="SSL connection timed out")
        except Exception as e:
            return SSLInfo(valid=False, error=str(e))

    def _fetch_robots(self, url: str) -> Optional[str]:
        """Fetch robots.txt content."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            response = httpx.get(robots_url, timeout=10, follow_redirects=True)
            if response.status_code == 200:
                content = response.text
                # Limit size
                return content[:5000] if len(content) > 5000 else content
        except Exception as e:
            logger.debug(f"Failed to fetch robots.txt: {e}")

        return None

    def _check_sitemap(self, url: str) -> tuple[bool, Optional[str]]:
        """Check if sitemap.xml exists and return its URL."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Common sitemap locations
        sitemap_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap/sitemap.xml",
            "/sitemaps/sitemap.xml",
        ]

        for path in sitemap_paths:
            sitemap_url = f"{base_url}{path}"
            try:
                response = httpx.head(sitemap_url, timeout=10, follow_redirects=True)
                if response.status_code == 200:
                    # Verify it's XML
                    content_type = response.headers.get("content-type", "")
                    if "xml" in content_type or path.endswith(".xml"):
                        return True, sitemap_url
            except Exception:
                continue

        # Check robots.txt for sitemap directive
        robots = self._fetch_robots(url)
        if robots:
            for line in robots.split("\n"):
                if line.lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    if sitemap_url:
                        return True, sitemap_url

        return False, None

    def check_url_status(self, url: str) -> Dict[str, any]:
        """
        Quick check of URL status without full probe.

        Args:
            url: URL to check

        Returns:
            Dict with status_code and response_time
        """
        try:
            with httpx.Client(follow_redirects=True, timeout=10) as client:
                response = client.head(url)
                return {
                    "url": url,
                    "status_code": response.status_code,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    "final_url": str(response.url),
                }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
            }
