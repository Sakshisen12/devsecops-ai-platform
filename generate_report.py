import json
import os
from jinja2 import Environment, FileSystemLoader

def build_report():
    print("📊 Generating HTML Security Audit Dashboard...")

    # Load Bandit Results
    bandit_issues = []
    total_flaws = 0
    if os.path.exists("bandit_results.json"):
        try:
            with open("bandit_results.json", "r") as f:
                bandit_data = json.load(f)
                bandit_issues = bandit_data.get("results", [])
                total_flaws = len(bandit_issues)
        except Exception as e:
            print(f"Error reading bandit_results.json: {e}")

    # Load AI Review Results
    ai_review = {
        "summary": "AI Review unavailable.",
        "security_flaws": [],
        "code_suggestions": []
    }
    if os.path.exists("ai_review.json"):
        try:
            with open("ai_review.json", "r") as f:
                ai_review = json.load(f)
        except Exception as e:
            print(f"Error reading ai_review.json: {e}")

    # Calculate simple Security Score (Base 100 minus 15 per security flaw)
    security_score = max(0, 100 - (total_flaws * 15))
    status = "PASSED" if total_flaws == 0 else "ACTION REQUIRED"

    # Render Jinja2 HTML Template
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.html")

    html_content = template.render(
        status=status,
        security_score=security_score,
        total_flaws=total_flaws,
        bandit_issues=bandit_issues,
        ai_review=ai_review
    )

    # Save output to index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ Dashboard successfully created: index.html")

if __name__ == "__main__":
    build_report()