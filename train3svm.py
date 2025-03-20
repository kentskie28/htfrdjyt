import json
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from torch.optim import lr_scheduler
from nltk_util import tokenize, stem, bag_of_words

with open('data/intents.json', 'r', encoding='utf-8') as f:
    intents = json.load(f)

all_words = []
tags = []
xy = []
ignore_words = ['?', '!', '.', ',']

for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        all_words.extend(w)
        xy.append((w, tag))

all_words = [stem(w) for w in all_words if w not in ignore_words]
all_words = sorted(set(all_words))
tags = sorted(set(tags))

X = []
y = []
for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence, all_words)
    X.append(bag)
    y.append(tags.index(tag))

X = np.array(X)
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(NeuralNet, self).__init__()
        self.l1 = nn.Linear(input_size, hidden_size)
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.l2 = nn.Linear(hidden_size, hidden_size)
        self.bn2 = nn.BatchNorm1d(hidden_size)
        self.l3 = nn.Linear(hidden_size, hidden_size)
        self.bn3 = nn.BatchNorm1d(hidden_size)
        self.l4 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.LeakyReLU()
        self.dropout = nn.Dropout(p=0.4)
    
    def forward(self, x):
        out = self.l1(x)
        if out.shape[0] > 1: 
            out = self.bn1(out)
        out = self.relu(out)
        out = self.dropout(out)
        
        out = self.l2(out)
        if out.shape[0] > 1:
            out = self.bn2(out)
        out = self.relu(out)
        out = self.dropout(out)

        out = self.l3(out)
        if out.shape[0] > 1:
            out = self.bn3(out)
        out = self.relu(out)
        out = self.dropout(out)
        
        out = self.l4(out)
        return out

# Hyperparameters
input_size = len(X_train[0])
hidden_size = 256  # Increased hidden size for more learning capacity
output_size = len(tags)
learning_rate = 0.0001  # Lower learning rate for finer training
num_epochs = 1000
batch_size = 32
patience = 100

# Dataset and DataLoader
class ChatDataset(Dataset):
    def __init__(self, X, y):
        self.n_samples = len(X)
        self.x_data = X
        self.y_data = y

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples

dataset = ChatDataset(X_train, y_train)
train_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True)

model = NeuralNet(input_size, hidden_size, output_size)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-6)
scheduler = lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=10)

best_accuracy = 0
epochs_no_improve = 0
for epoch in range(num_epochs):
    model.train()
    for (words, labels) in train_loader:
        words = words.clone().detach().float()
        labels = labels.clone().detach().long()

        outputs = model(words)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
        y_pred = model(X_test_tensor)
        _, predicted = torch.max(y_pred, 1)
        accuracy = accuracy_score(y_test, predicted.numpy())
        scheduler.step(accuracy)

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if (epoch + 1) % 100 == 0:
            print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}, Accuracy: {accuracy:.4f}')

print('Final Classification Report:\n', classification_report(y_test, predicted, labels=np.arange(len(tags)), target_names=tags))
print('Final Overall Accuracy:', best_accuracy)

model_data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,
    "tags": tags
}

FILE = "neural_model.pth"
torch.save(model_data, FILE)

print('Training complete. Model saved to neural_model.pth')
