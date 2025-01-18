from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import os
import json
import time
from Initialize_db import initialize_session_data

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join("instance", ".env"))

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize session data
DB_PATH = initialize_session_data()
MOODS_PATH = os.path.join("data", "mascot_moods.json")

# Load mascot personalities
with open(MOODS_PATH, "r") as f:
    mascot_moods = json.load(f)

# Allowed emotions
ALLOWED_EMOTIONS = ["neutral", "cool", "surprised", "happy", "angry"]

@app.route('/conversation', methods=['POST'])
def conversation():
    """Handles user input and responds with GPT-4."""
    try:
        data = request.json
        mascot = data["mascot"].lower()
        user_input = data["input"]

        # Load session data
        with open(DB_PATH, "r") as f:
            session_data = json.load(f)

        if mascot not in session_data:
            return jsonify({"error": "Invalid mascot"}), 400

        # Store the first message if it's not already stored
        if "initial_message" not in session_data:
            session_data["initial_message"] = user_input

        # Prepare conversation context with initial message
        initial_message = session_data.get("initial_message", "No idea provided yet")
        recent_messages = session_data[mascot]["messages"][-5:]  # Last 5 messages
        prompt = f"""
        You are {mascot_moods[mascot]["character"]}, focusing on {mascot_moods[mascot]["agenda"]}.
        Always remember the initial idea: "{initial_message}".
        Current conversation: {recent_messages}
        User: {user_input}
        Respond as {mascot_moods[mascot]["character"]}.
        """

        # GPT-4 API Call
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
        )
        message = gpt_response["choices"][0]["message"]["content"]

        # Extract mood
        mood = "neutral"  # Default mood
        if "--" in message:
            parts = message.split("--")
            message = parts[0].strip()
            extracted_mood = parts[1].strip().lower()
            if extracted_mood in ALLOWED_EMOTIONS:
                mood = extracted_mood

        # Update session data
        session_data[mascot]["messages"].append({"role": "user", "content": user_input})
        session_data[mascot]["messages"].append({"role": "assistant", "content": message})
        session_data[mascot]["mood"] = mood
        session_data[mascot]["last_active"] = str(int(time.time()))  # Update timestamp

        # Save updated session data
        with open(DB_PATH, "w") as f:
            json.dump(session_data, f)

        return jsonify({"message": message, "mood": mood})
    except Exception as e:
        print(f"Error in /conversation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/summary', methods=['POST'])
def summary():
    """Generates a summary of the pitch session."""
    try:
        # Load session data
        with open(DB_PATH, "r") as f:
            session_data = json.load(f)

        # Generate summary
        summary = "Final Summary:\n"
        for mascot, data in session_data.items():
            if mascot == "initial_message":
                continue
            last_message = data['messages'][-1]['content'] if data['messages'] else "No interaction"
            summary += f"{mascot.capitalize()} ({data['mood']}): {last_message}\n"

        # Debugging: Log summary
        print(f"Generated summary: {summary}")

        return jsonify({"summary": summary})
    except Exception as e:
        # Log and return the error
        print(f"Error in /summary: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Debugging: Verify API key
    print("Loaded API Key:", openai.api_key if openai.api_key else "No API key found")
    app.run(debug=True)