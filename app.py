import json
import subprocess
import os
import time
import random
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from chat import get_response

app = Flask(__name__)
CORS(app)

app.secret_key = 'admin'
SUPERUSER_CREDENTIALS = {
    "username": "admin",
    "password": "admin"
}
INTENTS_FILE = 'intents.json'
DESTINATIONS_FILE = 'destinations.json'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_FILE = os.path.join(BASE_DIR, 'data', 'intents.json')
INTENTSPH_FILE = os.path.join(BASE_DIR, 'data', 'intentsph.json')
DESTINATIONS_FILE = os.path.join(BASE_DIR, 'static', 'destinations.json')

with open(DESTINATIONS_FILE, 'r') as f:
    destinations_data = json.load(f)
    print(f"Destinations data loaded: {destinations_data}")

@app.get("/")
def index_get():
    return render_template("base.html", timestamp=time.time())

LOG_FILE = "chat_log.json"  # Log file to store interactions

def log_interaction(user_input, bot_response):
    log_entry = {
        "timestamp": str(datetime.datetime.now()),
        "user_input": user_input,
        "bot_response": bot_response
    }
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Error logging interaction: {e}")

# ✅ Load Logs from File
def load_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return [json.loads(line) for line in f.readlines()]
    except FileNotFoundError:
        return []

# ✅ Save Logs Back to File
def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")

# ✅ Function to Find Intent Tag
def find_intent_tag(bot_response):
    """Finds the intent tag based on the bot's response."""
    try:
        with open(INTENTS_FILE, "r", encoding='utf-8') as f:
            intents = json.load(f)

        print(f"Checking response: {bot_response}")  # Debugging output

        for intent in intents["intents"]:
            for response in intent["responses"]:
                if bot_response.strip().lower() == response.strip().lower():
                    print(f"Found tag: {intent['tag']} for response: {bot_response}")
                    return intent["tag"]

    except Exception as e:
        print(f"Error finding intent tag: {e}")

    print(f"No tag found for response: '{bot_response}' - Consider adding it to intents.json.")
    return "?"  # Return '?' if no tag is found

@app.route("/view_map")
def view_map():
    lat = request.args.get("lat", None)
    lon = request.args.get("lon", None)
    destination = request.args.get("destination", "")

    return render_template("map.html", lat=lat, lon=lon, destination=destination)


@app.route("/logs")
def get_logs():
    logs = load_logs()

    for log in logs:
        log["intent_tag"] = find_intent_tag(log["bot_response"])  # Assign intent tag

    return jsonify(logs)

@app.route("/edit_log", methods=["POST"])
def edit_log():
    data = request.json
    logs = load_logs()

    if 0 <= data["index"] < len(logs):
        new_user_input = data["newUserInput"]
        new_bot_response = data["newBotResponse"]
        new_intent_tag = data["newIntentTag"]

        logs[data["index"]]["user_input"] = new_user_input
        logs[data["index"]]["bot_response"] = new_bot_response
        logs[data["index"]]["intent_tag"] = new_intent_tag

        save_logs(logs)

        return jsonify({"message": "Log updated successfully!"})

    return jsonify({"error": "Invalid log index"}), 400

# Route to Render Logs Page
@app.route("/logs_page")
def logs_page():
    return render_template("logs.html")

@app.route("/api/get_tags", methods=["GET"])
def get_tags():
    """Fetch all available intent tags"""
    try:
        with open(INTENTS_FILE, "r") as f:
            intents = json.load(f)
        
        tags = [intent["tag"] for intent in intents["intents"]]
        return jsonify({"tags": tags})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/predict")
def predict():
    data = request.get_json()
    text = data.get("message")
    print(f"Received message: {text}")

    # Default to English intents
    response_data = get_response(text, user_id="default_user")  # No language argument

    message = {
        "answer": response_data["response"],
        "secondary_response": response_data.get("secondary_response"),
        "destination": response_data.get("destination"),
        "context": response_data.get("context"),
        "suggestion": response_data.get("suggestions", [])
    }

    log_interaction(text, message["answer"])
    
    return jsonify(message)

@app.route('/get_pattern', methods=['POST'])
def get_pattern():
    tag = request.json.get("tag")
    
    with open(INTENTS_FILE, 'r') as f:
        intents = json.load(f)

    for intent in intents['intents']:
        if intent['tag'].lower() == tag.lower():
            pattern = random.choice(intent['patterns']) 
            return jsonify({"pattern": pattern})
    
    return jsonify({"pattern": None})

@app.post("/get_destination")
def get_destination():
    data = request.get_json()
  

    destination_name = data.get("destination").lower().strip()
    print(f"Looking for destination: {destination_name}")  
    matching_destinations = [
        d for d in destinations_data['destinations']
        if destination_name in d['name'].lower().strip()
    ]
    
    if matching_destinations:
        destination = matching_destinations[0]  
        print(f"Found destination: {destination}")  
        return jsonify({
            'lat': destination['destinationlat'],
            'lon': destination['destinationlon'],
            'name': destination['name']
        })
    else:
        print(f"Destination not found: {destination_name}") 
    
    return jsonify({'lat': None, 'lon': None})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/get_data', methods=['GET'])
def get_data():
    try:
        with open(INTENTS_FILE, 'r') as f:
            intents = json.load(f)
        return jsonify({'intents': intents})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_intents', methods=['POST'])
def update_intents():
    try:
        data = request.json
        with open(INTENTS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({'message': 'Intents updated successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == SUPERUSER_CREDENTIALS['username'] and password == SUPERUSER_CREDENTIALS['password']:
            session['superuser'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('superuser', None)
    return redirect(url_for('index_get'))

@app.route('/superuser_dashboard')
def superuser_dashboard():
    if not session.get('superuser'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/add-intent', methods=['POST'])
def add_intent():
    data = request.get_json()
    try:
        with open(INTENTS_FILE, 'r') as file:
            intents = json.load(file)
        
        new_intent = {
            "tag": data.get('tag', ''),
            "patterns": data.get('patterns', []),
            "responses": data.get('responses', []),
            "secondary_responses": data.get('secondary_responses', []),
            "context": data.get('context', ''),
            "suggestions": data.get('suggestions', [])
        }

        intents['intents'].append(new_intent)

        with open(INTENTS_FILE, 'w') as file:
            json.dump(intents, file, indent=4)

        return jsonify({"success": True, "message": "Intent added successfully!"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "message": "Failed to add intent."})
    
@app.route('/api/intents', methods=['GET'])
def get_intents():
    try:
        with open('data/intents.json', 'r', encoding='utf-8') as file:
            intents_data = json.load(file)
        print("Intents data:", intents_data)
        return jsonify(intents_data['intents'])  
    except FileNotFoundError:
        return jsonify({"error": "intents.json file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/settings', methods=['GET'])
def settings_page():
    return render_template('settings.html')

@app.route('/update_settings', methods=['POST'])
def update_settings():
    data = request.json
    title = data.get('title', 'NISU AI')
    nav_color = data.get('navColor', '#00258b')
    content = data.get('content', '')

    with open('templates/index.html', 'r') as file:
        html = file.read()

    updated_html = html.replace('<title>NISU AI</title>', f'<title>{title}</title>')

    updated_html = updated_html.replace(
        'background-color: rgb(0, 36, 199);', f'background-color: {nav_color};'
    )

    if '<!-- CONTENT_PLACEHOLDER -->' in updated_html:
        updated_html = updated_html.replace(
            '<!-- CONTENT_PLACEHOLDER -->', content
        )

    with open('templates/index.html', 'w') as file:
        file.write(updated_html)

    return jsonify({'message': 'Settings updated successfully!'})

@app.route('/edit_base', methods=['GET', 'POST'])
def edit_base():
    base_path = 'templates/base.html'
    if request.method == 'POST':
        # Save the updated HTML
        updated_content = request.form.get('html_content')
        with open(base_path, 'w') as file:
            file.write(updated_content)
        return jsonify({"message": "Saved successfully!"})
    else:
        # Load the current HTML content
        with open(base_path, 'r') as file:
            html_content = file.read()
        return render_template('base.html', content=html_content)

@app.route("/delete_logs", methods=["POST"])
def delete_logs():
    data = request.json
    logs = load_logs()

    if "indexes" in data:
        indexes_to_delete = sorted(data["indexes"], reverse=True)
    elif "index" in data:  # Handle single index deletion
        indexes_to_delete = [data["index"]]
    else:
        return jsonify({"error": "Invalid request"}), 400

    for index in indexes_to_delete:
        if 0 <= index < len(logs):
            logs.pop(index)

    save_logs(logs)
    return jsonify({"message": "Log(s) deleted successfully!"})


@app.route("/add_to_intents", methods=["POST"])
def add_to_intents():
    data = request.json
    user_input = data.get("userInput")
    bot_response = data.get("botResponse")
    tag = data.get("tag")  # Get custom tag
    suggestions = data.get("suggestions", [])  # Get custom suggestions

    try:
        with open(INTENTS_FILE, "r") as f:
            intents = json.load(f)

        # Check if the tag already exists
        tag_exists = False
        for intent in intents["intents"]:
            if intent["tag"] == tag:
                intent["patterns"].append(user_input)
                tag_exists = True
                break

        # If no existing tag, create a new intent
        if not tag_exists:
            intents["intents"].append({
                "tag": tag,
                "patterns": [user_input],
                "responses": [bot_response],
                "context": "",
                "suggestions": suggestions
            })

        with open(INTENTS_FILE, "w") as f:
            json.dump(intents, f, indent=4)

        return jsonify({"message": f"Successfully added to intents.json under tag '{tag}'!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/save_base_html', methods=['POST'])
def save_base_html():
    data = request.get_json()
    html_content = data.get('htmlContent')
    
    with open('templates/base.html', 'r') as file:
        base_html = file.read()

    updated_html = base_html 
    updated_html = updated_html.replace('<section class="vision">', html_content)  
    # Save the updated HTML back to the file
    with open('templates/base.html', 'w') as file:
        file.write(updated_html)

    return jsonify({"success": True})

@app.route('/train', methods=['GET', 'POST'])
def train_model():
    if request.method == 'POST':
        try:
            # Execute the train.py script
            result = subprocess.run(['python', 'train.py'], capture_output=True, text=True)
            
            output = result.stdout
            error = result.stderr
            
            # Debug: Log the result of the training script
            print("Training output:", output)
            print("Training error:", error)
            
            if result.returncode == 0:
                return jsonify({"success": True, "message": "Training completed successfully!", "output": output})
            else:
                return jsonify({"success": False, "message": "Error during training.", "error": error})
        
        except Exception as e:
            print("Exception occurred:", e)
            return jsonify({"success": False, "message": str(e)})

    # If it's a GET request, render the training page
    return render_template('train.html')


if __name__ == "__main__":
    app.run(debug=True)
