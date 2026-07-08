import requests
from typing import List, Dict, Optional, Any
from sentry_mirror.logger import logger

def audit_security_headers(url: str) -> Dict[str, Any]:
    try:
        # Use a HEAD request to check headers without downloading the full body
        response = requests.head(url, timeout=10, allow_redirects=True)
        headers = response.headers

        # Security headers to check
        check_list = [
            'Content-Security-Policy',
            'Strict-Transport-Security',
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Referrer-Policy',
            'Permissions-Policy'
        ]

        results = {
            "url": url,
            "date": headers.get('Date', 'N/A'),
            "headers": {}
        }

        for header in check_list:
            status = "PRESENT" if header in headers else "MISSING"
            value = headers.get(header, "N/A")
            results["headers"][header] = {
                "status": status,
                "value": value
            }

        return results

    except Exception as e:
        logger.error(f"Error auditing {url}: {e}")
        return {"error": str(e)}

def format_audit_report(results: Dict[str, Any]) -> str:
    if "error" in results:
        return f"Error auditing {results.get('url')}: {results['error']}"

    report = []
    report.append(f"--- Security Audit Report: {results['url']} ---")
    report.append(f"Date: {results['date']}")
    report.append("-" * 40)

    for header, info in results["headers"].items():
        report.append(f"{header:25}: {info['status']}")
        if info['status'] == "PRESENT":
            report.append(f"  Value: {info['value']}")

    return "\n".join(report)

def run_security_audit(url: str, output_file: str):
    results = audit_security_headers(url)
    report = format_audit_report(results)

    try:
        with open(output_file, "w") as f:
            f.write(report)
        logger.info(f"Audit complete. Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save audit report: {e}")
