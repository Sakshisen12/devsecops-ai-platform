import json
import os
from jinja2 import Environment, FileSystemLoader

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
                    for vuln in res.get("Vulnerabilities", []):
                        trivy_issues.append({
                            "id": vuln.get("VulnerabilityID"),
                            "pkg": vuln.get("PkgName"),
                            "severity": vuln.get("Severity"),
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

    total_flaws = len(bandit_issues) + len(trivy_issues)
    security_score = max(0, 100 - (len(bandit_issues) * 15) - (len(trivy_issues) * 5))
    status = "PASSED" if total_flaws == 0 else "ACTION REQUIRED"

    # Render Jinja2 HTML Template
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.html")

    html_content = template.render(
        status=status,
        security_score=security_score,
        total_flaws=total_flaws,
        bandit_issues=bandit_issues,
        trivy_issues=trivy_issues,
        ai_review=ai_review
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ Dashboard successfully updated with Trivy container findings!")

if __name__ == "__main__":
    build_report()