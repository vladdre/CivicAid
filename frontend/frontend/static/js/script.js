let currentConversationId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadConversations();

    // Allow submitting with Enter (but Shift+Enter for newline)
    const textarea = document.getElementById('message-input');
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Focus input
    textarea.focus();
});

function autoResize(textarea) {
    textarea.style.height = 'auto'; // Reset height
    textarea.style.height = textarea.scrollHeight + 'px';
}

async function loadConversations() {
    const list = document.getElementById('history-list');
    try {
        const response = await fetch('/api/conversations');
        const conversations = await response.json();

        list.innerHTML = '';
        conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = `history-item ${conv.id === currentConversationId ? 'active' : ''}`;

            // Title Span
            const titleSpan = document.createElement('span');
            titleSpan.className = 'history-title';
            titleSpan.innerText = conv.title;
            titleSpan.onclick = () => loadChat(conv.id);

            // Delete Button
            const delBtn = document.createElement('button');
            delBtn.className = 'delete-btn';
            delBtn.innerHTML = '&times;'; // Multiplication sign x
            delBtn.onclick = (e) => {
                e.stopPropagation(); // Prevent loading chat
                if (confirm('Delete this chat?')) {
                    deleteChat(conv.id);
                }
            };

            item.appendChild(titleSpan);
            item.appendChild(delBtn);
            list.appendChild(item);
        });
    } catch (error) {
        console.error("Error loading conversations:", error);
    }
}

async function deleteChat(id) {
    try {
        const response = await fetch(`/api/conversations/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // Check if we deleted the current chat
            if (currentConversationId === id) {
                startNewChat();
            } else {
                loadConversations(); // Just reload list content
            }
        } else {
            console.error("Failed to delete chat");
        }
    } catch (error) {
        console.error("Error deleting chat:", error);
    }
}

async function loadChat(id) {
    currentConversationId = id;

    // Update active class in sidebar
    const items = document.querySelectorAll('.history-item');
    items.forEach(item => item.classList.remove('active'));
    // Ideally we would find the specific element by ID or re-render, 
    // but for simplicity we re-load conversations or just rely on re-clicking updating visually on reload if needed.
    // For now, let's just fetch messages.
    loadConversations(); // Re-render to update active state properly or we could implement manual toggle.

    const chatArea = document.getElementById('chat-area');
    chatArea.innerHTML = ''; // Clear current chat

    try {
        const response = await fetch(`/api/conversations/${id}`);
        const messages = await response.json();

        messages.forEach(msg => {
            appendMessage(msg.role, msg.content);
        });

        scrollToBottom();

    } catch (error) {
        console.error("Error loading chat:", error);
    }
}

function startNewChat() {
    currentConversationId = null;
    document.getElementById('chat-area').innerHTML = `
        <div class="welcome-message" id="welcome-message">
            <h1>ChatGPT Clone</h1>
        </div>
    `;
    loadConversations(); // Update active state
    document.getElementById('message-input').focus();
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    if (!content) return;

    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Remove welcome message if exists
    const welcome = document.getElementById('welcome-message');
    if (welcome) welcome.remove();

    // Show user message immediately
    appendMessage('user', content);
    scrollToBottom();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: content,
                conversation_id: currentConversationId
            })
        });

        const data = await response.json();

        // Show AI response
        appendMessage('assistant', data.ai_message);

        // If this was a new conversation, update ID and reload sidebar
        if (!currentConversationId) {
            currentConversationId = data.conversation_id;
        }
        loadConversations();
        scrollToBottom();

    } catch (error) {
        console.error("Error sending message:", error);
        appendMessage('assistant', "Error: Could not reach server.");
    }
}

function appendMessage(role, content) {
    const chatArea = document.getElementById('chat-area');
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avatar = role === 'user' ? 'U' : 'AI';
    const avClass = role === 'user' ? 'user-av' : 'ai-av'; // Add specific classes for color

    div.innerHTML = `
        <div class="message-content">
            <div class="avatar ${avClass}">${avatar}</div>
            <div class="text">${escapeHtml(content)}</div>
        </div>
    `;

    chatArea.appendChild(div);
}

function scrollToBottom() {
    const chatArea = document.getElementById('chat-area');
    chatArea.scrollTop = chatArea.scrollHeight;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function (m) { return map[m]; });
}
