document.addEventListener("DOMContentLoaded", function() {
    class Chatbox {
        constructor() {
            this.args = {
                openButton: document.querySelector('.chatbox__button'),
                chatBox: document.querySelector('.chatbox__support'),
                sendButton: document.querySelector('.send__button'),
            };
    
            this.state = false;
            this.messages = [];
            this.isSending = false;
        }
    
        display() {
            const { openButton, chatBox, sendButton } = this.args;
            const exitButton = chatBox.querySelector('.chatbox__exit');
            const textField = chatBox.querySelector('input');
        
            openButton.addEventListener('click', () => {
                this.toggleState(chatBox);
                openButton.style.display = 'none';
            });
        
            exitButton.addEventListener('click', () => {
                this.toggleState(chatBox);
                openButton.style.display = 'block';
            });
        
            sendButton.addEventListener('click', () => this.onSendButton(chatBox));
        
            textField.addEventListener("keyup", (event) => {
                if (event.key === "Enter") {
                    this.onSendButton(chatBox);
                }
            });
        }
        
        toggleState(chatbox) {
            this.state = !this.state;
            chatbox.classList.toggle('chatbox--active', this.state);
        }
    
        onSendButton(chatbox) {
            if (this.isSending) return;
        
            this.isSending = true;
            var textField = chatbox.querySelector('input');
            let text1 = textField.value;
        
            if (text1 === "") {
                this.isSending = false;
                return;
            }
        
            let msg1 = { name: "User", message: text1 };
            this.messages.push(msg1);
            this.updateChatText(chatbox);
        
            textField.value = '';
            this.sendMessageToBot(text1, chatbox);
        }
        
        sendMessageToBot(text, chatbox) {
            fetch('http://192.168.83.214:5000/predict', {
                method: 'POST',
                body: JSON.stringify({ message: text }),
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then((r) => r.json())
            .then((r) => {
                const { answer, secondary_response, suggestion } = r;
                console.log("Response from server:", r);
        
                this.messages.push({ name: "NISUBOT", message: answer });
                this.isSending = false;
                this.updateChatText(chatbox);
        
                if (secondary_response) {
                    setTimeout(() => {
                        this.messages.push({ name: "NISUBOT", message: secondary_response });
                        this.updateChatText(chatbox);
                    }, 2000);
                }
        
                if (suggestion && suggestion.length > 0) {
                    this.generateSuggestionButtons(chatbox, suggestion);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                this.isSending = false;
            });
        }    
        
        generateSuggestionButtons(chatbox, suggestions) {
            const chatmessage = chatbox.querySelector('.chatbox__messages');
        
            const suggestionContainer = document.createElement('div');
            suggestionContainer.className = 'suggested-replies';
        
            suggestions.forEach((suggestion) => {
                if (!suggestion.toLowerCase().includes("view map")) {
                    const button = document.createElement('button');
                    button.className = 'suggestion-button';
                    button.textContent = suggestion;
        
                    button.addEventListener('click', () => {
                        this.onSendSuggestion(chatbox, suggestion);
                    });
        
                    suggestionContainer.appendChild(button);
                }
            });
        
            chatmessage.prepend(suggestionContainer);
            chatmessage.scrollTop = chatmessage.scrollHeight;
        }
        onSendSuggestion(chatbox, suggestion) {
            console.log(`Suggestion clicked: ${suggestion}`);
            const textField = chatbox.querySelector('input');
            textField.value = suggestion;  // Directly use suggestion text
            this.onSendButton(chatbox);
        }
        updateChatText(chatbox) {
            let html = '';
            this.messages.slice().reverse().forEach((item) => {
                if (item.name === "NISUBOT") {
                    html += `<div class="messages__item messages__item--visitor">${item.message}</div>`;
                } else {
                    html += `<div class="messages__item messages__item--operator">${item.message}</div>`;
                }
            });
        
            const chatmessage = chatbox.querySelector('.chatbox__messages');
        
            if (chatmessage) {
                chatmessage.innerHTML = html;
                chatmessage.scrollTop = chatmessage.scrollHeight;
            }
        }
    }      
    
    document.addEventListener("DOMContentLoaded", () => {
        const chatbox = new Chatbox();
        chatbox.display();
    });
    });
    