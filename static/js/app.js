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
        this.firstInteractionCompleted = false;
    }
    
    display() {
        const { openButton, chatBox, sendButton } = this.args;
        const exitButton = chatBox.querySelector('.chatbox__exit');
    
        console.log('chatBox reference:', chatBox);
    
        openButton.addEventListener('click', () => {
            this.toggleState(chatBox);
            openButton.style.display = 'none';
            // Initialize the conversation when the chat is opened
            this.initializeConversation(chatBox);
        });
    
        exitButton.addEventListener('click', () => {
            this.toggleState(chatBox);
            openButton.style.display = 'block'; 
        });
    
        sendButton.addEventListener('click', () => this.onSendButton(chatBox));
    
        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                this.onSendButton(chatBox);
            }
        });

        const suggestionButtons = chatBox.querySelectorAll('.start-suggestion-button'); 
        suggestionButtons.forEach((button) => { 
            button.addEventListener('click', () => {
                const userInput = button.getAttribute('data-input'); 
                const textField = chatBox.querySelector('input');
                textField.value = userInput;
                this.onSendButton(chatBox);
                this.hideStartSuggestions(chatBox);
            });
        });
    }

    // Add new method to initialize conversation
    initializeConversation(chatbox) {
        // Add the initial greeting message
        const initialMessage = "Hi I'm NISUBOT! your chatbot assistant for directional and procedural";
        this.messages.push({ name: "NISUBOT", message: initialMessage });
        this.updateChatText(chatbox);
        
        // Make sure the welcome message and buttons are visible
        const welcomeMessage = chatbox.querySelector('#welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'block';
        }
        
        const startSuggestionContainer = chatbox.querySelector('.start-suggestion-container');
        if (startSuggestionContainer) {
            startSuggestionContainer.style.display = 'flex';
        }
    }

    toggleState(chatbox) {
        this.state = !this.state;
        if (this.state) {
            chatbox.classList.add('chatbox--active');
        } else {
            chatbox.classList.remove('chatbox--active');
            location.reload();
        }
    }

    hideWelcomeMessage(chatbox) {
        const welcomeMessage = chatbox.querySelector('#welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
    }
    
    // Add new method to hide start suggestions
    hideStartSuggestions(chatbox) {
        if (this.firstInteractionCompleted) {
            return; // Don't hide if already hidden
        }
        
        const startSuggestionContainer = chatbox.querySelector('.start-suggestion-container');
        if (startSuggestionContainer) {
            startSuggestionContainer.style.display = 'none';
        }
        
        this.firstInteractionCompleted = true;
    }

    redirectToMap() {
        const currentLocation = JSON.parse(sessionStorage.getItem("currentLocation"));
        const destination = sessionStorage.getItem("destination");

        if (currentLocation && destination) {
            const url = new URL(window.location.origin + "/view_map");
            url.searchParams.append("lat", currentLocation.latitude);
            url.searchParams.append("lon", currentLocation.longitude);
            url.searchParams.append("destination", destination);
            window.location.href = url;
        } else {
            alert("Location or destination is missing. Ensure geolocation is enabled.");
        }
    }

    onStartButton(chatbox) {
        const textField = chatbox.querySelector('input');
        textField.value = "Directional";
        this.onSendButton(chatbox);
        this.hideWelcomeMessage(chatbox);
    }
        
    onSendButton(chatbox) {
        if (this.isSending) return;

        this.isSending = true;
        var textField = chatbox.querySelector('input');
        let text1 = textField.value;
        let language = document.getElementById("language-select").value;

        if (text1 === "") {
            this.isSending = false;
            return;
        }

        let msg1 = { name: "User", message: text1 };
        this.messages.push(msg1);
        this.updateChatText(chatbox);

        this.hideWelcomeMessage(chatbox);
        this.hideStartSuggestions(chatbox);

        textField.value = '';
        this.sendMessageToBot(text1, language, chatbox);
    }

    sendMessageToBot(text, language, chatbox) {
        fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            body: JSON.stringify({ message: text, language: language }),
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then((r) => r.json())
        .then((r) => {
            const { answer, secondary_response, suggestion } = r;
            console.log("Response from server:", r);
            let botResponse = r.answer;
            let secondaryResponse = r.secondary_response; 
            let destination = r.destination;

            setTimeout(() => {
                this.messages.push({ name: "NISUBOT", message: answer });
                this.isSending = false;
                this.suggestions = suggestion; 
                this.updateChatText(chatbox);
            }, 0);
    
            if (secondary_response) {
                setTimeout(() => {
                    this.messages.push({ name: "NISUBOT", message: secondary_response });
                    this.updateChatText(chatbox);
                }, 2000);
            }
    
            if (suggestion && suggestion.length > 0) {
                this.generateSuggestionButtons(chatbox, suggestion);
            }

            if (botResponse.includes("It seems that you are asking for location, please click the map button to redirect you to your destination")) {
                this.requestGeolocation(chatbox, destination);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            this.isSending = false;
        });
    }

    requestGeolocation(chatbox, destination) {
        console.log("Executing requestGeolocation, destination:", destination);

        const chatmessage = chatbox.querySelector(".chatbox__messages");

        if (!chatmessage) {
            console.error("Chatbox messages container not found! Button cannot be added.");
            return;
        }

        console.log("✅ Chat message container found:", chatmessage);

        // Remove existing button if already present
        const existingButton = chatmessage.querySelector(".map-button");
        if (existingButton) {
            console.log("⚠️ Removing existing map button before adding a new one.");
            existingButton.parentNode.remove();
        }

        // Create container for the button
        const buttonContainer = document.createElement("div");
        buttonContainer.className = "messages__item messages__item--visitor";

        // Create the button
        const button = document.createElement("button");
        button.className = "map-button";
        button.innerHTML = `<i class='fas fa-map'></i> Click me to View Map`;

        // Force visibility
        button.style.display = "block";
        button.style.marginTop = "10px";
        button.style.padding = "10px";
        button.style.backgroundColor = "#007bff";
        button.style.color = "#fff";
        button.style.border = "none";
        button.style.borderRadius = "5px";
        button.style.cursor = "pointer";

        // Store destination if available
        if (destination) {
            sessionStorage.setItem("destination", destination);
        } else {
            console.warn("⚠️ No destination provided, button will still appear.");
        }

        // Add event listener to redirect to the map
        button.addEventListener("click", () => {
            redirectToMap();
        });

        // Append the button to the container
        buttonContainer.appendChild(button);

        // Use setTimeout to ensure it's added **after** chat updates
        setTimeout(() => {
            chatmessage.appendChild(buttonContainer);
            chatmessage.scrollTop = chatmessage.scrollHeight; // Scroll to latest message
            console.log("✅ Map button successfully added:", button);
        }, 500);  // Delay to prevent overwriting
    }
    
    generateSuggestionButtons(chatbox, suggestions) {
        const chatmessage = chatbox.querySelector('.chatbox__messages');
    
        const suggestionContainer = document.createElement('div');
        suggestionContainer.className = 'suggested-replies'; 
    
        suggestions.forEach((suggestion) => {
            const button = document.createElement('button');
            button.className = 'suggestion-button';
            button.textContent = suggestion;
    
            button.addEventListener('click', () => {
                this.onSendSuggestion(chatbox, suggestion);
            });
    
            suggestionContainer.appendChild(button);
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
            if (item.isMap) {
                html += item.message; 
            } else if (item.name === "NISUBOT") {
                html += `<div class="messages__item messages__item--visitor">${item.message}</div>`;
            } else {
                html += `<div class="messages__item messages__item--operator">${item.message}</div>`;
            }
        });
    
        const chatmessage = chatbox.querySelector('.chatbox__messages');
    
        if (chatmessage) {
            chatmessage.innerHTML = html;
    
            // Add back the welcome message and suggested buttons if they exist
            const welcomeMessage = document.getElementById('welcome-message');
            if (welcomeMessage && !this.firstInteractionCompleted) {
                chatmessage.appendChild(welcomeMessage);
            }
            
            const startSuggestionContainer = document.querySelector('.start-suggestion-container');
            if (startSuggestionContainer && !this.firstInteractionCompleted) {
                chatmessage.appendChild(startSuggestionContainer);
            }
            
            chatmessage.scrollTop = chatmessage.scrollHeight;
        }
    
        if (this.suggestions && this.suggestions.length > 0) {
            this.generateSuggestionButtons(chatbox, this.suggestions);
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const chatbox = new Chatbox();
    chatbox.display();
});

function redirectToMap() {
    const destination = sessionStorage.getItem("destination") || "";

    const url = new URL(window.location.origin + "/view_map"); 
    if (destination) {
        url.searchParams.append("destination", destination);
    }

    console.log("Redirecting to:", url.toString());
    window.location.href = url;
}

document.addEventListener("DOMContentLoaded", function () {
    const chatboxButton = document.querySelector(".chatbox__button");
    const chatbox = document.querySelector(".chatbox__support");
    const chatboxExit = document.querySelector(".chatbox__exit");
    const footer = document.getElementById("footer");

    // Open Chatbox
    chatboxButton.addEventListener("click", () => {
        chatbox.classList.add("chatbox--active");
        footer.style.display = "none"; // Hide footer
    });

    // Close Chatbox
    chatboxExit.addEventListener("click", () => {
        chatbox.classList.remove("chatbox--active");
        footer.style.display = "block"; // Show footer
    });
});