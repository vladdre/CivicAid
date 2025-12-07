let currentConversationId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadConversations();

    // Restore sidebar state
    const sidebar = document.querySelector('.sidebar');
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true' && sidebar) {
        sidebar.classList.add('collapsed');
    }

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
            <h1>CivicAID</h1>
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

    // Show loading indicator
    showLoadingIndicator();

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

        // Hide loading indicator
        hideLoadingIndicator();

        // Show AI response with typewriter effect
        appendMessageWithTypewriter('assistant', data.ai_message);

        // If this was a new conversation, update ID
        if (!currentConversationId) {
            currentConversationId = data.conversation_id;
        }
        
        // Reload conversations to update title in sidebar
        loadConversations();
        scrollToBottom();

    } catch (error) {
        console.error("Error sending message:", error);
        hideLoadingIndicator();
        appendMessage('assistant', "Error: Could not reach server.");
    }
}

function appendMessage(role, content) {
    const chatArea = document.getElementById('chat-area');
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avClass = role === 'user' ? 'user-av' : 'ai-av';
    
    // For user, show first letter of username (like in sidebar), for assistant show logo image
    let avatarHtml;
    if (role === 'user') {
        const userInitial = typeof USERNAME !== 'undefined' && USERNAME.length > 0 ? USERNAME[0].toUpperCase() : 'U';
        avatarHtml = '<div class="avatar ' + avClass + '">' + userInitial + '</div>';
    } else {
        const logoPath = typeof AI_RESPONSE_LOGO !== 'undefined' ? AI_RESPONSE_LOGO : '/static/images/response_logo.png';
        avatarHtml = '<div class="avatar ' + avClass + '"><img src="' + logoPath + '" alt="AI" class="ai-avatar-img"></div>';
    }

    div.innerHTML = `
        <div class="message-content">
            ${avatarHtml}
            <div class="text">${escapeHtml(content)}</div>
        </div>
    `;

    chatArea.appendChild(div);
}

function appendMessageWithTypewriter(role, content) {
    const chatArea = document.getElementById('chat-area');
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avClass = role === 'user' ? 'user-av' : 'ai-av';
    
    // For assistant show logo image
    const logoPath = typeof AI_RESPONSE_LOGO !== 'undefined' ? AI_RESPONSE_LOGO : '/static/images/response_logo.png';
    const avatarHtml = '<div class="avatar ' + avClass + '"><img src="' + logoPath + '" alt="AI" class="ai-avatar-img"></div>';

    div.innerHTML = `
        <div class="message-content">
            ${avatarHtml}
            <div class="text typewriter-text"></div>
        </div>
    `;

    chatArea.appendChild(div);
    const textElement = div.querySelector('.typewriter-text');
    
    // Typewriter effect - write text character by character
    const escapedContent = escapeHtml(content);
    let index = 0;
    const speed = 2; // milliseconds per character (adjust for speed: lower = faster)
    
    function typeWriter() {
        if (index < escapedContent.length) {
            textElement.textContent = escapedContent.substring(0, index + 1);
            textElement.textContent = escapedContent.substring(0, index + 1);
            index++;
            setTimeout(typeWriter, speed);
            // Auto-scroll while typing
            scrollToBottom();
        }
    }
    
    typeWriter();
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

function showLoadingIndicator() {
    const chatArea = document.getElementById('chat-area');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading-indicator';
    loadingDiv.className = 'message assistant loading-message';
    
    loadingDiv.innerHTML = `
        <div class="message-content">
            <div class="avatar ai-av">
                <img src="${typeof AI_RESPONSE_LOGO !== 'undefined' ? AI_RESPONSE_LOGO : '/static/images/response_logo.png'}" alt="AI" class="ai-avatar-img">
            </div>
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <div class="loading-text">Consult legislatia...</div>
            </div>
        </div>
    `;
    
    chatArea.appendChild(loadingDiv);
    scrollToBottom();
}

function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        
        // Salvează starea în localStorage
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);
    }
}

