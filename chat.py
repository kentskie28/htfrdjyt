import json
import random
import torch
from model import NeuralNet
from nltk_util import bag_of_words, tokenize
from nltk.metrics.distance import edit_distance

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

FILE = "data.pth"
data = torch.load(FILE)
input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "Nisu"
context = {}
DESTINATIONS_FILE = 'static/destinations.json'

def load_destinations():
    try:
        with open(DESTINATIONS_FILE, 'r', encoding='utf-8') as f:
            destinations_data = json.load(f)
            return {d['name'].lower(): d for d in destinations_data['destinations']}
    except FileNotFoundError:
        print(f"Error: {DESTINATIONS_FILE} not found.")
        return {}

def load_intents(language):
    file_path = 'data/intentsph.json' if language == "tagalog" else 'data/intents.json'
    with open(file_path, 'r', encoding='utf-8') as json_data:
        return json.load(json_data)

def fuzzy_match(user_input, reference_words, threshold=0.7):
    corrected_input = []
    for word in user_input:
        if len(word) <= 3 or word in reference_words:
            corrected_input.append(word)
            continue
        best_match = min(reference_words, key=lambda w: edit_distance(word, w))
        similarity = 1 - (edit_distance(word, best_match) / max(len(word), len(best_match)))
        corrected_input.append(best_match if similarity > threshold else word)
    return corrected_input

def get_user_context(user_id):
    return context.get(user_id, None)

def set_user_context(user_id, new_context):
    context[user_id] = new_context

def get_response(msg, user_id="default_user"):
    intents = load_intents("english")
    destinations = load_destinations()
    sentence_tokens = tokenize(msg)
    corrected_tokens = fuzzy_match(sentence_tokens, all_words, threshold=0.75)
    
    X = bag_of_words(corrected_tokens, all_words).reshape(1, -1)
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]
    prob = torch.softmax(output, dim=1)[0][predicted.item()]

    confidence_threshold = 0.75
    if prob.item() > confidence_threshold:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                primary_response = random.choice(intent['responses'])
                suggestions = intent.get("suggestions", [])
                
                return {
                    "response": primary_response,
                    "destination": None,
                    "suggestions": suggestions
                }
    
    # Destination Check
    for word in corrected_tokens:
        if word.lower() in destinations:
            return {
                "response": f"I found information about {word}. Would you like details?",
                "destination": destinations[word.lower()],
                "suggestions": []
            }
    
    return {
        "response": "I'm not sure what you mean. Can you rephrase? You can ask about directions, locations, or services.",
        "destination": None,
    }

if __name__ == "__main__":
    print("Let's chat! (type 'quit' to exit)")
    while True:
        sentence = input("You: ")
        if sentence == "quit":
            break
        resp = get_response(sentence)
        print(resp)
