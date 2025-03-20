import json
import random
import joblib

bot_name = "Nisu"
context = {}

DESTINATIONS_FILE = 'static/destinations.json'

# Load Destinations
def load_destinations():
    try:
        with open(DESTINATIONS_FILE, 'r', encoding='utf-8') as f:
            destinations_data = json.load(f)
            return [d['name'].lower() for d in destinations_data['destinations']]
    except FileNotFoundError:
        print(f"Error: {DESTINATIONS_FILE} not found.")
        return []

# Load Intents
def load_intents(language):
    file_path = 'data/intentsph.json' if language == "tagalog" else 'data/intents.json'
    with open(file_path, 'r', encoding='utf-8') as json_data:
        return json.load(json_data)

# User Context Management
def get_user_context(user_id):
    return context.get(user_id, None)

def set_user_context(user_id, new_context):
    context[user_id] = new_context

# Redefine Tokenizer and Load Vectorizer & Model
def advanced_tokenizer(text):
    import re
    text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
    tokens = [word for word in text.split() if len(word) > 1]
    return tokens

model_filename = 'optimized_svm_model.pkl'
vectorizer_filename = 'tfidf_vectorizer.pkl'
model = joblib.load(model_filename)
vectorizer = joblib.load(vectorizer_filename)
vectorizer.tokenizer = advanced_tokenizer

# Get Response
def get_response(msg, user_id="default_user"):
    intents = load_intents("english")
    possible_destinations = load_destinations()

    X = vectorizer.transform([msg])
    predicted = model.predict(X)[0]
    prob = max(model.predict_proba(X)[0])

    confidence_threshold = 0.75
    print(f"[DEBUG] Prediction: {predicted}, Confidence: {prob * 100:.2f}%")

    if prob > confidence_threshold:
        for intent in intents['intents']:
            if predicted == intent["tag"]:
                suggestions = intent.get("suggestions", [])
                primary_response = random.choice(intent['responses'])
                secondary_responses = intent.get('secondary_responses', [])
                secondary_response = random.choice(secondary_responses) if secondary_responses else None
                return {
                    "response": primary_response,
                    "destination": None,
                    "secondary_response": secondary_response,
                    "suggestions": suggestions
                }

    return {
        "response": "I don't understand.",
        "destination": None,
        "secondary_response": None,
        "suggestions": []
    }

if __name__ == "__main__":
    print("Let's chat! (type 'quit' to exit)")
    while True:
        sentence = input("You: ")
        if sentence.lower() == "quit":
            break
        resp = get_response(sentence)
        print(resp)
