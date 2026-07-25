import os
import json
import sys
from google import genai

def review_code_with_gemini():
    # Fetch the API key from environment variables (will be set in pipeline/local terminal)
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("⚠️ Warning: GEMINI_API_KEY environment variable not set.")
        # Provide a fallback message for testing without API key
        fallback_review = {
            "summary": "Skipped AI Review: GEMINI_API_KEY is missing.",
            "suggestions": ["Set GEMINI_API_KEY to enable automated AI code reviews."]
        }
        with open("ai_review.json", "w") as f:
            json.dump(fallback_review, f, indent=2)
        return

    # Check if target app file exists
    target_file = "app.py"
    if not os.path.exists(target_file):
        print(f"Error: {target_file} not found.")
        sys.exit(1)

    # Read the contents of app.py
    with open(target_file, "r") as f:
        source_code = f.read()

    print(f"🔍 Sending {target_file} to Gemini API for AI code review...")

    # Initialize Gemini Client using google-genai library
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
        # Call Gemini 2.5 Flash model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Clean up response text in case markdown blocks are returned
        cleaned_text = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        review_data = json.loads(cleaned_text)

        # Save AI review to JSON file
        with open("ai_review.json", "w") as f:
            json.dump(review_data, f, indent=2)

        print("✅ Gemini AI code review successfully saved to ai_review.json!")

    except Exception as e:
        print(f"❌ Error during Gemini API call: {e}")
        # Save error state so pipeline still completes gracefully
        error_data = {
            "summary": f"AI Review Error: {str(e)}",
            "security_flaws": ["Unable to complete AI scan."],
            "code_suggestions": ["Verify API key and network connectivity."]
        }
        with open("ai_review.json", "w") as f:
            json.dump(error_data, f, indent=2)

if __name__ == "__main__":
    review_code_with_gemini()