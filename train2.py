import json
import numpy as np
from nltk_util import tokenize, stem
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, log_loss, classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
import pickle

with open('data/intents.json', 'r', encoding='utf-8') as f:
    intents = json.load(f)

all_sentences = []
all_labels = []

for intent in intents['intents']:
    tag = intent['tag']
    for pattern in intent['patterns']:
        tokenized_sentence = tokenize(pattern)
        stemmed_sentence = " ".join(stem(w) for w in tokenized_sentence)
        all_sentences.append(stemmed_sentence)
        all_labels.append(tag)

vectorizer = TfidfVectorizer(
    tokenizer=tokenize,
    stop_words='english',
    ngram_range=(1, 3),
    max_features=1000
)
X = vectorizer.fit_transform(all_sentences)

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(all_labels)

class_weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
class_weights_dict = {i: weight for i, weight in enumerate(class_weights)}

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

param_grid = {'alpha': [0.1, 0.3, 0.5, 1.0]}
model = MultinomialNB()
grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train, y_train)

best_model = grid_search.best_estimator_

best_model.fit(X_train, y_train)

y_pred = best_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred, output_dict=True, zero_division=1)
conf_matrix = confusion_matrix(y_test, y_pred)

print(f'Accuracy: {accuracy:.4f}')
print('Classification Report:')
print(classification_report(y_test, y_pred, zero_division=1))
print(conf_matrix)

cv_scores = cross_val_score(best_model, X, y, cv=5, scoring='accuracy')
print(f'Cross-Validation Accuracy: {np.mean(cv_scores):.4f} + {np.std(cv_scores):.4f}')

with open('optimized_nb_model.pkl', 'wb') as f:
    pickle.dump((best_model, vectorizer, label_encoder), f)

print('Optimized Model saved as optimized_nb_model.pkl')
