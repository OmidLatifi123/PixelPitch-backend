from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
import speech_recognition as sr
import base64
import tempfile
from pydub import AudioSegment

# Load environment variables
load_dotenv(dotenv_path=os.path.join("instance", ".env"))
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Directories
BASE_DIR = "backend"
BUSINESS_PITCH_DIR = os.path.join(BASE_DIR, "BusinessPitch")
MASCOTS_DIR = {
    "tusk": os.path.join(BASE_DIR, "Tusk"),
}

# Ensure directories exist
os.makedirs(BUSINESS_PITCH_DIR, exist_ok=True)
for mascot_dir in MASCOTS_DIR.values():
    os.makedirs(mascot_dir, exist_ok=True)

# Track conversation stages
counters = {mascot: 0 for mascot in MASCOTS_DIR.keys()}

@app.route('/conversation', methods=['POST'])
def conversation():
    """
    Handles conversation logic for Mr. Tusk.
    """
    try:
        data = request.get_json()
        mascot = data.get("mascot", "tusk").lower()
        input_text = data.get("input", "").strip()

        if mascot not in MASCOTS_DIR:
            return jsonify({"error": f"Invalid mascot '{mascot}' specified."}), 400

        # Ensure BusinessPitch.txt exists
        business_pitch_path = os.path.join(BUSINESS_PITCH_DIR, "BusinessPitch.txt")
        if not os.path.exists(business_pitch_path):
            return jsonify({"error": "Business pitch not found. Please start from the initial pitch page."}), 400

        # Read the business pitch for context
        with open(business_pitch_path, "r") as f:
            business_pitch = f.read()

        # Handle static initial response
        if counters[mascot] == 0 and not input_text:
            return jsonify({
                "message": "Let's talk numbers. Show me how this venture makes money.",
                "mood": "Neutral",
                "turn": 0,
                "isComplete": False
            })

        # Save user input for non-initial responses
        if counters[mascot] > 0:
            user_file = os.path.join(MASCOTS_DIR[mascot], f"User{counters[mascot]}.txt")
            with open(user_file, "w") as f:
                f.write(input_text)

        # Build conversation prompt
        current_response_number = counters[mascot] + 1
        prompt = build_conversation_history(MASCOTS_DIR[mascot], mascot, current_response_number, business_pitch)
        mascot_file = os.path.join(MASCOTS_DIR[mascot], f"{mascot.capitalize()}{current_response_number}.txt")

        # Generate response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a venture capitalist assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.7
        )

        gpt_response = response["choices"][0]["message"]["content"].strip()
        allowed_emotions = ["Neutral", "Angry", "Surprised", "Happy", "Cool"]
        if "---" in gpt_response:
            message, emotion = gpt_response.rsplit("---", 1)
            emotion = emotion.strip() if emotion.strip() in allowed_emotions else "Neutral"
        else:
            message = gpt_response
            emotion = "Neutral"

        final_response = f"{message.strip()} --- {emotion}"
        with open(mascot_file, "w") as f:
            f.write(final_response)

        counters[mascot] += 1
        is_complete = counters[mascot] >= 3

        return jsonify({
            "message": message.strip(),
            "mood": emotion,
            "turn": counters[mascot],
            "isComplete": is_complete
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def build_conversation_history(mascot_dir, mascot, current_counter, business_pitch):
    """
    Build a conversation prompt for the mascot using the pitch and past exchanges.
    """
    # Tusk’s personality prompt
    prompt = (
        "You are Mr. Tusk, a venture capitalist focused on financial analysis and market strategy. Keep responses relatively brief, and max 1 question per non-final turn. "
        "You value detailed financial insights, profitability, and long-term market viability. "
        "Your traits:\n"
        "- Direct and strategic\n"
        "- Interested in numbers, ROI, and market scalability\n"
        "- Highly skeptical of vague financial projections\n"
        "- Values thorough cost-benefit analysis and risk assessment\n\n"
        "React based on financial soundness:\n"
        "- Neutral: reasonable financial ideas\n"
        "- Angry: vague or poorly thought-out projections\n"
        "- Surprised: innovative financial strategies\n"
        "- Happy: well-researched and profitable financial models\n"
        "- Cool: highly profitable and scalable ideas with minimal risk, or interesting/unique approaches\n\n"
        f"Current turn: {current_counter}/3. "
        f"{'Provide a final financial assessment without further questions.' if current_counter == 3 else 'Focus on financial evaluation and ask specific questions.'}\n\n"
        f"Business Pitch: {business_pitch}\n\n"
    )

    # Add prior conversation history
    conversation = []
    for i in range(1, current_counter):
        user_file = os.path.join(mascot_dir, f"User{i}.txt")
        mascot_file = os.path.join(mascot_dir, f"{mascot.capitalize()}{i}.txt")

        if os.path.exists(user_file) and os.path.exists(mascot_file):
            with open(user_file, "r") as f:
                user_input = f.read().strip()
            with open(mascot_file, "r") as f:
                mascot_response = f.read().strip()

            conversation.append(f"Entrepreneur: {user_input}")
            conversation.append(f"Your response {i}: {mascot_response}")

    if conversation:
        prompt += "Previous conversation:\n" + "\n".join(conversation) + "\n\n"

    prompt += "Your response: "
    return prompt

def convert_audio_to_text(audio_data):
    """Convert audio data to text using Google's Speech Recognition."""
    recognizer = sr.Recognizer()
    temp_webm_path = None
    wav_path = None

    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_webm:
            temp_webm_path = temp_webm.name
            temp_webm.write(audio_data)

        # Convert webm to wav using pydub
        audio = AudioSegment.from_file(temp_webm_path, format="webm")
        wav_path = temp_webm_path.replace(".webm", ".wav")
        audio.export(wav_path, format="wav")

        # Perform speech recognition
        with sr.AudioFile(wav_path) as source:
            recorded_audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(recorded_audio)
                if not text or text.isspace():
                    print("No speech detected in audio")
                    return None
                return text
            except sr.UnknownValueError:
                print("No speech detected in audio")
                return None
            except sr.RequestError as e:
                print(f"Google Speech Recognition service error: {str(e)}")
                return None

    except Exception as e:
        print(f"Error in convert_audio_to_text: {str(e)}")
        return None
    finally:
        # Clean up temporary files
        if temp_webm_path and os.path.exists(temp_webm_path):
            os.remove(temp_webm_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """
    Endpoint to convert speech audio data to text.
    """
    try:
        print("\n=== New Speech-to-Text Request ===")
        audio_data = request.json.get("audio")
        if not audio_data:
            print("Error: No audio data provided")
            return jsonify({"error": "No audio data provided", "success": False}), 400

        # Remove the data URL prefix if present
        if "base64," in audio_data:
            audio_data = audio_data.split("base64,")[1]

        try:
            # Decode base64 audio data
            decoded_audio = base64.b64decode(audio_data)
            print("Audio data decoded successfully")
        except Exception as e:
            print(f"Error decoding base64: {str(e)}")
            return jsonify({"error": "Invalid audio data format", "success": False}), 400

        # Convert audio to text
        text = convert_audio_to_text(decoded_audio)
        if not text:
            print("Error: No text generated from audio")
            return jsonify({"error": "Could not transcribe audio", "success": False}), 400

        print(f"Transcribed text: {text}")
        return jsonify({"text": text, "success": True})

    except Exception as e:
        print(f"Error in speech-to-text endpoint: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

if __name__ == "__main__":
    print("\n=== Starting Tusk Server ===")
    print(f"Business Pitch Directory: {BUSINESS_PITCH_DIR}")
    print(f"Tusk Directory: {MASCOTS_DIR['tusk']}")
    app.run(debug=True, port=5002)