import json
import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import accuracy_score
from nltk_util import tokenize, stem, bag_of_words
from model import NeuralNet
from torch.utils.data import Dataset, DataLoader

# Load intents
with open('data/intents.json', 'r', encoding='utf-8') as f:
    intents = json.load(f)

all_words = []
tags = []
xy = []

for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        all_words.extend(w)
        xy.append((w, tag))

# Stem and lower words, remove duplicates
ignore_words = ['?', '!', '.', ',']
all_words = [stem(w) for w in all_words if w not in ignore_words]
all_words = sorted(set(all_words))
tags = sorted(set(tags))

X_train = []
y_train = []

for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence, all_words)
    X_train.append(bag)
    label = tags.index(tag)
    y_train.append(label)

X_train = np.array(X_train)
y_train = np.array(y_train)

input_size = len(X_train[0])
hidden_size = 8
output_size = len(tags)
learning_rate = 0.001
num_epochs = 1000
batch_size = 8

class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples

# DataLoader
dataset = ChatDataset()
train_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True)

# Model, Loss, Optimizer
model = NeuralNet(input_size, hidden_size, output_size)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

print(len(xy), "patterns")
print(len(tags), "tags:", tags)
print(len(all_words), "unique stemmed words:", all_words)

# Training loop
for epoch in range(num_epochs):
    for (words, labels) in train_loader:
        words = torch.tensor(words, dtype=torch.float32)
        labels = torch.tensor(labels, dtype=torch.long)

        outputs = model(words)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    if (epoch + 1) % 100 == 0:
        # Evaluate accuracy during training
        with torch.no_grad():
            outputs = model(torch.tensor(X_train, dtype=torch.float32))
            _, predicted = torch.max(outputs, 1)
            accuracy = accuracy_score(y_train, predicted.numpy())
            print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}, Accuracy: {accuracy:.4f}')

# Compute final overall accuracy
with torch.no_grad():
    outputs = model(torch.tensor(X_train, dtype=torch.float32))
    _, predicted = torch.max(outputs, 1)
    final_accuracy = accuracy_score(y_train, predicted.numpy())

print(f'Final Overall Accuracy: {final_accuracy:.4f}')

# Save the model
model_data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,
    "tags": tags
}

FILE = "data.pth"
torch.save(model_data, FILE)

print('Training complete. Model saved to data.pth')
