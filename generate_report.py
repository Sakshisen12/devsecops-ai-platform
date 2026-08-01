import json
import os
from jinja2 import Environment, FileSystemLoader

# Severity weights used to compute the security score.
# Trivy scans of any real base image turn up dozens of LOW/MEDIUM OS-package
# CVEs that aren't practically exploitable in this context, so those barely
# move the score. HIGH/CRITICAL findings (in either tool) are what should
# actually tank it.
BANDIT_WEIGHTS = {"HIGH": 15, "MEDIUM": 7, "LOW": 2}
# The pipeline now scans with --severity HIGH,CRITICAL --ignore-unfixed, so
# MEDIUM/LOW and no-fix-available CVEs are filtered out before this even runs.
# What's left is a small list of things that are both serious and actionable,
# so each one is weighted more heavily than before.
TRIVY_WEIGHTS = {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 2, "LOW": 0}


def build_report():
    print("📊 Generating HTML Security Audit Dashboard...")

    # 1. Load Bandit Results
    bandit_issues = []
    if os.path.exists("bandit_results.json"):
        try:
            with open("bandit_results.json", "r") as f:
                bandit_data = json.load(f)
                bandit_issues = bandit_data.get("results", [])
        except Exception as e:
            print(f"Error reading bandit_results.json: {e}")

    # 2. Load Trivy Results
    trivy_issues = []
    if os.path.exists("trivy_results.json"):
        try:
            with open("trivy_results.json", "r") as f:
                trivy_data = json.load(f)
                results = trivy_data.get("Results", [])
                for res in results:
                    for vuln in res.get("Vulnerabilities", []) or []:
                        trivy_issues.append({
                            "id": vuln.get("VulnerabilityID"),
                            "pkg": vuln.get("PkgName"),
                            "severity": vuln.get("Severity", "UNKNOWN"),
                            "title": vuln.get("Title", "No title provided")
                        })
        except Exception as e:
            print(f"Error reading trivy_results.json: {e}")

    # 3. Load AI Review Results
    ai_review = {"summary": "AI Review unavailable.", "security_flaws": [], "code_suggestions": []}
    if os.path.exists("ai_review.json"):
        try:
            with open("ai_review.json", "r") as f:
                ai_review = json.load(f)
        except Exception as e:
            print(f"Error reading ai_review.json: {e}")

    # --- Counts ---
    bandit_count = len(bandit_issues)
    trivy_count = len(trivy_issues)
    total_flaws = bandit_count + trivy_count

    trivy_severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for issue in trivy_issues:
        sev = issue["severity"] if issue["severity"] in trivy_severity_counts else "UNKNOWN"
        trivy_severity_counts[sev] += 1

    # Only surface HIGH/CRITICAL Trivy findings in the detail list — LOW/MEDIUM
    # OS-package noise is summarized as a count instead of listed line by line.
    trivy_issues_notable = [
        i for i in trivy_issues if i["severity"] in ("CRITICAL", "HIGH")
    ]

    # --- Severity-weighted security score ---
    # Code and container findings are scored as two separate 100-point pools,
    # then averaged. Scoring them from one shared pool lets a noisy base-image
    # CVE count (often outside your control — no fix available upstream yet)
    # drown out a genuinely clean codebase, which isn't a fair signal.
    bandit_deductions = sum(
        BANDIT_WEIGHTS.get(issue.get("issue_severity", ""), 5) for issue in bandit_issues
    )
    trivy_deductions = sum(
        TRIVY_WEIGHTS.get(issue["severity"], 1) for issue in trivy_issues
    )

    code_score = max(0, 100 - bandit_deductions)
    container_score = max(0, 100 - trivy_deductions)
    security_score = round((code_score + container_score) / 2)

    # Build fails on HIGH bandit / CRITICAL trivy already (pipeline gates) —
    # this status reflects that same bar for the dashboard badge.
    has_blocking_findings = (
        any(i.get("issue_severity") == "HIGH" for i in bandit_issues)
        or trivy_severity_counts["CRITICAL"] > 0
    )
    status = "ACTION REQUIRED" if has_blocking_findings else "PASSED"

    # Render Jinja2 HTML Template
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.html")

    html_content = template.render(
        status=status,
        security_score=security_score,
        total_flaws=total_flaws,
        bandit_count=bandit_count,
        trivy_count=trivy_count,
        bandit_issues=bandit_issues,
        trivy_issues=trivy_issues_notable,
        trivy_severity_counts=trivy_severity_counts,
        ai_review=ai_review
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ Dashboard successfully updated with Trivy container findings!")


if __name__ == "__main__":
    build_report()
