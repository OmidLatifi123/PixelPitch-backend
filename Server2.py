from flask import Flask, request, jsonify
from flask_cors import CORS  # Add this import
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

# Create necessary directories if they don't exist
os.makedirs(BUSINESS_PITCH_DIR, exist_ok=True)
for mascot_dir in MASCOTS_DIR.values():
    os.makedirs(mascot_dir, exist_ok=True)
    print(f"Created or verified directory: {mascot_dir}")

# Counter for keeping track of the conversation stage
counters = {mascot: 0 for mascot in MASCOTS_DIR.keys()}

def build_conversation_history(mascot_dir, mascot, current_counter):
    print(f"\n--- Building Conversation History ---")
    print(f"Mascot: {mascot}, Current Counter: {current_counter}")
    conversation = []
    
    # First, get the business pitch
    business_pitch_path = os.path.join(BUSINESS_PITCH_DIR, "BusinessPitch.txt")
    if os.path.exists(business_pitch_path):
        with open(business_pitch_path, "r") as f:
            business_pitch = f.read()
            print(f"Found Business Pitch: {business_pitch}")
    else:
        print("No business pitch file found")
        return ""
    
    # Start building the prompt
    prompt = (
        "You are Leo the Lion, a visionary, forward-thinker, and ambitious dreamer in the business world. "
        "You respond to business pitches with one of the following emotions: Neutral, Angry, Surprised, Happy, Cool. "
        "Your responses should reflect your personality and should be concise. "
        "Always end your response with '--- emotion', where 'emotion' is one of the allowed emotions. "
        "Ask engaging follow-up questions about the business idea.\n\n"
        f"*BusinessPitch*: {business_pitch}\n\n"
    )
    
    # Add conversation history
    print("\nChecking previous conversation files:")
    for i in range(1, current_counter):
        user_file = os.path.join(mascot_dir, f"User{i}.txt")
        mascot_file = os.path.join(mascot_dir, f"{mascot.capitalize()}{i}.txt")
        
        print(f"\nChecking files for turn {i}:")
        print(f"User file exists: {os.path.exists(user_file)}")
        print(f"Mascot file exists: {os.path.exists(mascot_file)}")
        
        # Only add message pairs that exist completely
        if os.path.exists(user_file) and os.path.exists(mascot_file):
            try:
                with open(mascot_file, "r") as f:
                    mascot_response = f.read().strip()
                with open(user_file, "r") as f:
                    user_response = f.read().strip()
                    
                if mascot_response and user_response:
                    print(f"Adding turn {i} to conversation:")
                    print(f"Mascot {i}: {mascot_response}")
                    print(f"User {i}: {user_response}")
                    conversation.append(f"{mascot.capitalize()}{i}: {mascot_response}")
                    conversation.append(f"User{i}: {user_response}")
            except Exception as e:
                print(f"Error reading conversation files for turn {i}: {e}")
                continue
    
    # Add all valid conversation entries to prompt
    if conversation:
        prompt += "\n".join(conversation) + "\n"
    
    # Add current turn marker
    prompt += f"{mascot.capitalize()}{current_counter}: "
    
    print(f"\nFinal Prompt:")
    print(prompt)
    return prompt

@app.route('/conversation', methods=['POST'])
def conversation():
    try:
        print("\n=== New Conversation Request ===")
        data = request.get_json()
        mascot = data.get("mascot", "lion").lower()
        input_text = data.get("input", "")
        
        print(f"Mascot: {mascot}")
        print(f"Input text: {input_text}")
        print(f"Current counter: {counters[mascot]}")

        if mascot not in MASCOTS_DIR:
            print(f"Error: Invalid mascot '{mascot}' specified")
            return jsonify({"error": f"Invalid mascot '{mascot}' specified."}), 400

        if not input_text:
            print("Error: No input provided")
            return jsonify({"error": "No input provided."}), 400

        # Store business pitch only on first message
        if counters[mascot] == 0:
            print("\n--- First Message - Setting up new conversation ---")
            business_pitch_path = os.path.join(BUSINESS_PITCH_DIR, "BusinessPitch.txt")
            with open(business_pitch_path, "w") as f:
                f.write(input_text)
            print(f"Saved business pitch: {input_text}")

            # Clean up any existing conversation files
            print("\nCleaning up old conversation files:")
            for i in range(1, 4):
                user_file = os.path.join(MASCOTS_DIR[mascot], f"User{i}.txt")
                mascot_file = os.path.join(MASCOTS_DIR[mascot], f"{mascot.capitalize()}{i}.txt")
                if os.path.exists(user_file):
                    os.remove(user_file)
                    print(f"Removed {user_file}")
                if os.path.exists(mascot_file):
                    os.remove(mascot_file)
                    print(f"Removed {mascot_file}")

        # Update the counter and set up paths
        counters[mascot] += 1
        print(f"\nIncremented counter to: {counters[mascot]}")
        user_file = os.path.join(MASCOTS_DIR[mascot], f"User{counters[mascot]}.txt")
        mascot_file = os.path.join(MASCOTS_DIR[mascot], f"{mascot.capitalize()}{counters[mascot]}.txt")

        # Save user input
        with open(user_file, "w") as f:
            f.write(input_text)
        print(f"Saved user input to: {user_file}")

        # Build the prompt using the helper function
        prompt = build_conversation_history(MASCOTS_DIR[mascot], mascot, counters[mascot])

        print("\n--- Calling GPT-4 API ---")
        # Call the GPT-4 model
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.7
        )

        # Extract GPT response
        gpt_response = response["choices"][0]["message"]["content"].strip()
        print(f"Raw GPT response: {gpt_response}")

        # Ensure response ends with one of the allowed emotions
        allowed_emotions = ["Neutral", "Angry", "Surprised", "Happy", "Cool"]
        if "---" in gpt_response:
            emotion_part = gpt_response.split("---")
            emotion = emotion_part[1].strip() if len(emotion_part) > 1 else "Neutral"
            if emotion not in allowed_emotions:
                print(f"Invalid emotion detected: {emotion}, defaulting to Neutral")
                emotion = "Neutral"
            message = emotion_part[0].strip()
        else:
            print("No emotion detected in response, defaulting to Neutral")
            emotion = "Neutral"
            message = gpt_response

        # Append the emotion to the message and save mascot response
        final_response = f"{message} --- {emotion}"
        with open(mascot_file, "w") as f:
            f.write(final_response)
        print(f"Saved mascot response to: {mascot_file}")

        print("\n--- Final Response ---")
        print(f"Message: {message}")
        print(f"Emotion: {emotion}")
        print(f"Turn: {counters[mascot]}")
        print(f"Is Complete: {counters[mascot] >= 3}")

        # Return response with turn count
        return jsonify({
            "message": message, 
            "mood": emotion, 
            "turn": counters[mascot],
            "isComplete": counters[mascot] >= 3
        })

    except Exception as e:
        print(f"\nERROR in conversation endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n=== Starting Server ===")
    print(f"Business Pitch Directory: {BUSINESS_PITCH_DIR}")
    print(f"Mascot Directories: {MASCOTS_DIR}")
    app.run(debug=True)