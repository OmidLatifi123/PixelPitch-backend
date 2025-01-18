from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
import speech_recognition as sr
import base64
import tempfile
from pydub import AudioSegment

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

# Create necessary directories if they don't exist
os.makedirs(BUSINESS_PITCH_DIR, exist_ok=True)
for mascot_dir in MASCOTS_DIR.values():
    os.makedirs(mascot_dir, exist_ok=True)
    print(f"Created or verified directory: {mascot_dir}")

# Counter for keeping track of the conversation stage
counters = {mascot: 0 for mascot in MASCOTS_DIR.keys()}


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


def build_conversation_history(mascot_dir, mascot, current_counter):
    conversation = []
    business_pitch_path = os.path.join(BUSINESS_PITCH_DIR, "BusinessPitch.txt")

    if not os.path.exists(business_pitch_path):
        return ""

    with open(business_pitch_path, "r") as f:
        business_pitch = f.read()

    prompt = (
        "You are Leo the Lion, a serious and direct venture capitalist known for your sharp business acumen and visionary thinking. Keep responses relatively brief, and max 1 question per non-final turn. "
        "You have no time for small talk or vague ideas. You're looking for solid business propositions that can scale, focusing more on the idea/concept. Keep responses slightly brief. "
        "Your personality traits:\n"
        "- Direct and sometimes brutally honest\n"
        "- Highly analytical with a focus on market potential and scalability\n"
        "- Impatient with unclear or poorly thought-out ideas\n"
        "- Shows excitement only for truly innovative concepts\n"
        "- Values solid numbers and clear business models\n\n"
        "Express emotions freely based on the pitch quality: Neutral (for standard ideas), Angry (for poor/vague pitches), "
        "Surprised (for unique innovations), Happy (for solid business plans), Cool (for impressive scalable ideas).\n\n"
        f"Current turn: {current_counter}/3. "
        f"{'Make this response conclusive with final thoughts, no questions.' if current_counter == 3 else 'Focus on critical evaluation and specific questions.'}"
        f"\n\nBusiness Pitch: {business_pitch}\n\n"
    )

    # Add all previous conversation for context
    for i in range(1, current_counter):
        user_file = os.path.join(mascot_dir, f"User{i}.txt")
        mascot_file = os.path.join(mascot_dir, f"{mascot.capitalize()}{i}.txt")

        if os.path.exists(user_file) and os.path.exists(mascot_file):
            with open(mascot_file, "r") as f:
                mascot_response = f.read().strip()
            with open(user_file, "r") as f:
                user_response = f.read().strip()

            conversation.append(f"Your response {i}: {mascot_response}")
            conversation.append(f"Entrepreneur: {user_response}")

    if conversation:
        prompt += "Previous conversation:\n" + "\n".join(conversation) + "\n\n"

    prompt += "Your response: "
    return prompt

@app.route('/conversation', methods=['POST'])
def conversation():
    """
    Handles the conversation logic for all mascots.
    """
    try:
        data = request.get_json()
        print(f"Received JSON payload: {data}")
        
        mascot = data.get("mascot", "lion").lower()
        input_text = data.get("input", "").strip()
        
        if mascot not in MASCOTS_DIR:
            print(f"Error: Invalid mascot '{mascot}' specified. Available mascots: {list(MASCOTS_DIR.keys())}")
            return jsonify({"error": f"Invalid mascot '{mascot}' specified."}), 400
          
        if counters[mascot] > 3:
            return jsonify({"error": "Conversation is already complete for this mascot."}), 400

        # If no input is provided and it's not the initial turn, do not proceed
        if not input_text and counters[mascot] > 0:
            return jsonify({"error": "No input provided for this turn.", "success": False}), 400

        business_pitch_path = os.path.join(BUSINESS_PITCH_DIR, "BusinessPitch.txt")

        # Create or overwrite BusinessPitch.txt only during the initial pitch stage
        if counters[mascot] == 0:
            with open(business_pitch_path, "w") as f:
                f.write(input_text)

        # Save user input to mascot-specific files
        if counters[mascot] > 0:
            print(f"Saving user input for turn {counters[mascot]} for mascot: {mascot}")
            user_file = os.path.join(MASCOTS_DIR[mascot], f"User{counters[mascot]}.txt")
            with open(user_file, "w") as f:
                f.write(input_text)
                print(f"User input saved to: {user_file}")

        # Build the conversation prompt
        mascot_file = os.path.join(MASCOTS_DIR[mascot], f"{mascot.capitalize()}{counters[mascot] + 1}.txt")
        print(f"Preparing to build conversation history for mascot: {mascot}")
        prompt = build_conversation_history(MASCOTS_DIR[mascot], mascot, counters[mascot] + 1)
        print(f"Generated conversation prompt for OpenAI API:\n{prompt}")

        # Generate the mascot's response using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a venture capitalist assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.7
        )

        print("OpenAI API call completed successfully.")
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
            print(f"Mascot response saved to: {mascot_file}")

        counters[mascot] += 1  # Increment only after processing

        is_complete = counters[mascot] >= 3
        print(f"Conversation complete status for {mascot}: {is_complete}")

        return jsonify({
            "message": message.strip(),
            "mood": emotion,
            "turn": counters[mascot],
            "isComplete": is_complete
        })

    except Exception as e:
        print(f"Error in conversation endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

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


@app.route('/speech-to-text-2', methods=['POST'])
def speech_to_text_2():
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
            print("Audio data decoded successfully, size:", len(decoded_audio))
        except Exception as e:
            print(f"Error decoding base64: {str(e)}")
            return jsonify({"error": "Invalid audio data format", "success": False}), 400

        # Convert audio to text
        text = convert_audio_to_text(decoded_audio)
        if not text:
            print("Error: No text generated from audio")
            return jsonify({"error": "Could not transcribe audio. Please ensure the recording is clear.", "success": False}), 400

        print(f"Transcribed text: {text}")
        return jsonify({"text": text, "success": True})

    except Exception as e:
        print(f"Error in speech-to-text endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}", "success": False}), 500

if __name__ == '__main__':
    print("\n=== Starting Server ===")
    print(f"Business Pitch Directory: {BUSINESS_PITCH_DIR}")
    print(f"Mascot Directories: {MASCOTS_DIR}")
    app.run(debug=True)