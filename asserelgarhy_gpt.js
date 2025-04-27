// === Global State ===
let userName = "";
let chatHistory = [];
let apiBaseUrl = "https://asserelgarhygpt.onrender.com"; // Your backend URL

// === DOM Elements ===
const loginButton = document.getElementById('google-login');
const sendButton = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatContainer = document.getElementById('chat-container');
const newChatButton = document.getElementById('new-chat');
const chatsList = document.getElementById('chats-list');
const imageButton = document.getElementById('generate-image');

// === Helper Functions ===

// Create a chat bubble
function createChatBubble(message, sender) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerText = message;
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Save chat to sidebar
function saveChatToSidebar(title, id) {
    const chatItem = document.createElement('div');
    chatItem.className = 'chat-item';
    chatItem.innerText = title;
    chatItem.onclick = () => loadChat(id);
    chatsList.appendChild(chatItem);
}

// Load old chat
function loadChat(id) {
    const oldChat = JSON.parse(localStorage.getItem(id));
    chatContainer.innerHTML = '';
    oldChat.forEach(entry => {
        createChatBubble(entry.message, entry.sender);
    });
}

// Save current chat to localStorage
function saveCurrentChat() {
    const chatId = `chat_${Date.now()}`;
    localStorage.setItem(chatId, JSON.stringify(chatHistory));
    saveChatToSidebar(chatHistory[0]?.message.substring(0, 20) || 'Chat', chatId);
}

// Reset for new chat
function startNewChat() {
    saveCurrentChat();
    chatHistory = [];
    chatContainer.innerHTML = '';
}

// === Main Actions ===

// Send message to backend
async function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;
    createChatBubble(message, 'user');
    chatHistory.push({ sender: 'user', message });

    userInput.value = "";

    try {
        const response = await fetch(`${apiBaseUrl}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, history: chatHistory })
        });
        const data = await response.json();

        if (data.reply) {
            createChatBubble(data.reply, 'bot');
            chatHistory.push({ sender: 'bot', message: data.reply });
        } else {
            createChatBubble("⚠️ Error: No reply.", 'bot');
        }
    } catch (err) {
        console.error(err);
        createChatBubble("⚠️ Error contacting server.", 'bot');
    }
}

// Google OAuth Login
async function loginWithGoogle() {
    window.location.href = `${apiBaseUrl}/login`; // Redirect to login
}

// Generate AI Image
async function generateImage() {
    const prompt = prompt("Describe the image you want me to create:");

    if (!prompt) return;

    try {
        const response = await fetch(`${apiBaseUrl}/generate-image`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });
        const data = await response.json();

        if (data.image_url) {
            const img = document.createElement('img');
            img.src = data.image_url;
            img.className = 'generated-image';
            chatContainer.appendChild(img);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        } else {
            createChatBubble("⚠️ Couldn't generate image.", 'bot');
        }
    } catch (err) {
        console.error(err);
        createChatBubble("⚠️ Error generating image.", 'bot');
    }
}

// === Event Listeners ===
sendButton.addEventListener('click', sendMessage);
newChatButton.addEventListener('click', startNewChat);
loginButton.addEventListener('click', loginWithGoogle);
imageButton.addEventListener('click', generateImage);

// === Initialization ===
function initApp() {
    const askName = prompt("👋 Welcome! Please enter your name:");
    userName = askName || "User";
    document.getElementById('greeting').innerText = `Hello, ${userName} 👋`;
}

initApp();
