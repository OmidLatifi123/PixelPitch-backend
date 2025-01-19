from flask import Flask, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join("instance", ".env"))

# Set the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Base directories
BASE_DIR = "backend"
BUSINESS_PITCH_DIR = os.path.join(BASE_DIR, "BusinessPitch")
MASCOTS_DIR = {
    "lion": os.path.join(BASE_DIR, "Lion"),
    "owl": os.path.join(BASE_DIR, "Owl"),
    "tusk": os.path.join(BASE_DIR, "Tusk"),
}

def get_final_response(mascot_dir, mascot):
    """Get the final response (text and emotion) from a mascot's directory."""
    try:
        # Look for the last response file (Lion3.txt, Owl3.txt, or Tusk3.txt)
        response_file = os.path.join(mascot_dir, f"{mascot.capitalize()}3.txt")
        
        if not os.path.exists(response_file):
            return None, None
            
        with open(response_file, "r") as f:
            content = f.read().strip()
            
        # Split the content into message and emotion
        if "---" in content:
            message, emotion = content.rsplit("---", 1)
            return message.strip(), emotion.strip()
        return content.strip(), "Neutral"
        
    except Exception as e:
        print(f"Error reading {mascot}'s final response: {str(e)}")
        return None, None

def get_business_pitch():
    """Get the original business pitch."""
    try:
        pitch_file = os.path.join(BUSINESS_PITCH_DIR, "BusinessPitch.txt")
        if not os.path.exists(pitch_file):
            return None
            
        with open(pitch_file, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading business pitch: {str(e)}")
        return None

@app.route('/generate-summary', methods=['GET'])
def generate_summary():
    """Generate a summary of the pitch and mascot responses."""
    try:
        # Get the business pitch
        business_pitch = get_business_pitch()
        if not business_pitch:
            return jsonify({"error": "Business pitch not found"}), 404

        # Get final responses from all mascots
        mascot_responses = {}
        for mascot, mascot_dir in MASCOTS_DIR.items():
            response, emotion = get_final_response(mascot_dir, mascot)
            if response and emotion:
                mascot_responses[mascot] = {
                    "response": response,
                    "mood": emotion
                }

        # If we don't have responses from all mascots, return an error
        if len(mascot_responses) != 3:
            return jsonify({"error": "Not all mascot responses are available"}), 400

        # Create the prompt for OpenAI
        prompt = f"""Analyze this business pitch and the feedback from three venture capitalists:

Business Pitch:
{business_pitch}

Venture Capitalist Feedback:
1. Leo the Lion (Direct and analytical VC):
Response: {mascot_responses['lion']['response']}
Mood: {mascot_responses['lion']['mood']}

2. Oliver the Owl (Risk-focused and detail-oriented VC):
Response: {mascot_responses['owl']['response']}
Mood: {mascot_responses['owl']['mood']}

3. Tommy the Tusk (Innovation-focused and market-oriented VC):
Response: {mascot_responses['tusk']['response']}
Mood: {mascot_responses['tusk']['mood']}

Please provide a concise summary (max 150 words) that:
1. Evaluates the overall reception of the pitch
2. Identifies key strengths and concerns raised
3. Provides a balanced conclusion based on all three VCs' perspectives
"""

        # Generate summary using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional business analyst synthesizing venture capitalist feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

        summary = response["choices"][0]["message"]["content"].strip()

        # Save the summary to a file
        summary_dir = os.path.join(BASE_DIR, "Summary")
        os.makedirs(summary_dir, exist_ok=True)
        summary_file = os.path.join(summary_dir, "Summary.txt")
        with open(summary_file, "w") as f:
            f.write(summary)

        return jsonify({
            "summary": summary,
            "mascot_responses": mascot_responses,
            "business_pitch": business_pitch
        })

    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n=== Starting Summary Server ===")
    print(f"Business Pitch Directory: {BUSINESS_PITCH_DIR}")
    print(f"Mascot Directories: {MASCOTS_DIR}")
    app.run(debug=True, port=5001)  # Using port 5001 to avoid conflict with main server