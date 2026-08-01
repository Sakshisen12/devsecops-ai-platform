import os
import json
import sys
from google import genai
from google.genai import errors as genai_errors


def review_code_with_gemini():
    # Fetch the API key from environment variables (will be set in pipeline/local terminal)
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("⚠️ Warning: GEMINI_API_KEY environment variable not set.")
        fallback_review = {
            "summary": "Skipped AI Review: GEMINI_API_KEY is missing.",
            "security_flaws": [],
            "code_suggestions": ["Set GEMINI_API_KEY to enable automated AI code reviews."]
        }
        with open("ai_review.json", "w") as f:
            json.dump(fallback_review, f, indent=2)
        return

    target_file = "app.py"
    if not os.path.exists(target_file):
        print(f"Error: {target_file} not found.")
        sys.exit(1)

    with open(target_file, "r") as f:
        source_code = f.read()

    print(f"🔍 Sending {target_file} to Gemini API for AI code review...")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are a Senior DevSecOps Engineer performing a code audit.
    Review the following Python code for security vulnerabilities, code smells, and performance bottlenecks:

    ```python
    {source_code}
    ```

    Please format your output strictly as a valid JSON object with the following structure:
    {{
      "summary": "A brief 2-sentence executive summary of code quality.",
      "security_flaws": ["List of identified security vulnerabilities"],
      "code_suggestions": ["Actionable refactoring suggestions or fixes"]
    }}
    Do not wrap response in markdown code blocks like ```json. Return raw JSON string only.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        cleaned_text = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        review_data = json.loads(cleaned_text)

        with open("ai_review.json", "w") as f:
            json.dump(review_data, f, indent=2)

        print("✅ Gemini AI code review successfully saved to ai_review.json!")

    except genai_errors.ClientError as e:
        # 400 FAILED_PRECONDITION with "User location is not supported" means the
        # calling IP (e.g. the Azure hosted build agent's datacenter) is in a region
        # Google's Generative Language API doesn't serve — not an issue with the
        # key, the code, or the pipeline logic itself.
        if "FAILED_PRECONDITION" in str(e) or "not supported" in str(e).lower():
            print(f"❌ Gemini API rejected the request due to a region restriction: {e}")
            error_data = {
                "summary": "AI review unavailable: Gemini API is not accessible from this build agent's region.",
                "security_flaws": [],
                "code_suggestions": [
                    "This is a known Google API region restriction on the hosted CI agent's IP, not an issue with the pipeline or the code. "
                    "Re-run the pipeline (agent region can vary between runs) or switch to Vertex AI with an explicit region to avoid this."
                ]
            }
        else:
            print(f"❌ Error during Gemini API call: {e}")
            error_data = {
                "summary": f"AI Review Error: {str(e)}",
                "security_flaws": ["Unable to complete AI scan."],
                "code_suggestions": ["Verify API key and network connectivity."]
            }
        with open("ai_review.json", "w") as f:
            json.dump(error_data, f, indent=2)

    except Exception as e:
        print(f"❌ Error during Gemini API call: {e}")
        error_data = {
            "summary": f"AI Review Error: {str(e)}",
            "security_flaws": ["Unable to complete AI scan."],
            "code_suggestions": ["Verify API key and network connectivity."]
        }
        with open("ai_review.json", "w") as f:
            json.dump(error_data, f, indent=2)


if __name__ == "__main__":
    review_code_with_gemini()
