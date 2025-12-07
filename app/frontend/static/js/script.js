let currentConversationId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadConversations();

    // Restore sidebar state
    const sidebar = document.querySelector('.sidebar');
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true' && sidebar) {
        sidebar.classList.add('collapsed');
    }

    // Restore theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeIcon(savedTheme);
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
    
    // Initialize speech recognition
    initSpeechRecognition();
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
                showDeleteConfirmation(conv.id, conv.title);
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
        // Silent error - no notification to user
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

function showDeleteConfirmation(chatId, chatTitle) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'delete-modal-overlay';
    overlay.id = 'delete-modal-overlay';
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'delete-modal';
    
    modal.innerHTML = `
        <div class="delete-modal-content">
            <h3>Ștergere conversație</h3>
            <p>Ești sigur că vrei să ștergi conversația "<strong>${escapeHtml(chatTitle)}</strong>"?</p>
            <p class="delete-warning">Această acțiune nu poate fi anulată.</p>
            <div class="delete-modal-buttons">
                <button class="delete-btn-cancel" onclick="closeDeleteModal()">Nu</button>
                <button class="delete-btn-confirm" onclick="confirmDeleteChat(${chatId})">Da</button>
            </div>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Close on overlay click
    overlay.onclick = (e) => {
        if (e.target === overlay) {
            closeDeleteModal();
        }
    };
    
    // Store chatId for confirmation
    overlay.dataset.chatId = chatId;
}

function closeDeleteModal() {
    const overlay = document.getElementById('delete-modal-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function confirmDeleteChat(chatId) {
    closeDeleteModal();
    deleteChat(chatId);
}

// Voice-to-text functionality
let recognition = null;
let isRecording = false;

// Initialize speech recognition
function initSpeechRecognition() {
    // Check if browser supports Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = true; // Continuă înregistrarea până când utilizatorul o oprește
        recognition.interimResults = true; // Afișează rezultate intermediare
        recognition.lang = 'ro-RO'; // Romanian language
        
        recognition.onstart = () => {
            isRecording = true;
            finalText = ''; // Resetează textul final la început
            updateVoiceButton(true);
        };
        
        // Stochează textul final pentru a evita duplicarea
        let finalText = '';
        
        recognition.onresult = (event) => {
            const textarea = document.getElementById('message-input');
            let interimTranscript = '';
            let newFinalTranscript = '';
            
            // Procesează doar rezultatele noi (optimizare)
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    newFinalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Actualizează doar dacă există text nou (optimizare)
            if (newFinalTranscript) {
                finalText += newFinalTranscript;
                textarea.value = finalText + interimTranscript;
                autoResize(textarea);
            } else if (interimTranscript) {
                // Actualizează doar interim pentru feedback rapid
                textarea.value = finalText + interimTranscript;
                autoResize(textarea);
            }
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            
            // Doar pentru erori critice, oprește înregistrarea
            if (event.error === 'not-allowed') {
                alert('Permisiunea pentru microfon a fost refuzată. Te rog să permți accesul la microfon.');
                isRecording = false;
                updateVoiceButton(false);
            } else if (event.error === 'no-speech') {
                // Nu oprește pentru "no-speech" - poate utilizatorul încă vorbește
                console.log('Nu s-a detectat vorbire. Continuă înregistrarea...');
            } else {
                // Pentru alte erori, oprește și încearcă fallback
                isRecording = false;
                updateVoiceButton(false);
                startBackendVoiceRecording();
            }
        };
        
        recognition.onend = () => {
            // Dacă înregistrarea este încă activă (utilizatorul nu a oprit-o), reîncepe rapid
            if (isRecording) {
                // Reîncepe imediat pentru continuitate
                setTimeout(() => {
                    if (isRecording) {
                        try {
                            recognition.start();
                        } catch (error) {
                            // Dacă nu poate reîncepe, oprește
                            isRecording = false;
                            updateVoiceButton(false);
                        }
                    }
                }, 100); // Delay mic pentru a evita erori
            } else {
                updateVoiceButton(false);
            }
        };
    } else {
        // Browser doesn't support Web Speech API, use backend
        console.log('Web Speech API not supported, using backend');
    }
}

function toggleVoiceRecording() {
    // If already recording via backend, stop it
    if (isRecording && mediaRecorder) {
        stopBackendVoiceRecording();
        return;
    }
    
    if (!recognition) {
        // Try to initialize
        initSpeechRecognition();
        if (!recognition) {
            // Use backend fallback
            startBackendVoiceRecording();
            return;
        }
    }
    
    if (isRecording) {
        recognition.stop();
        isRecording = false;
        updateVoiceButton(false);
    } else {
        try {
            recognition.start();
        } catch (error) {
            console.error('Error starting recognition:', error);
            // Fallback to backend
            startBackendVoiceRecording();
        }
    }
}

function updateVoiceButton(recording) {
    const voiceBtn = document.getElementById('voice-btn');
    const voiceIcon = document.getElementById('voice-icon');
    
    if (recording) {
        voiceBtn.classList.add('recording');
        // Change icon to stop icon
        voiceIcon.innerHTML = `
            <circle cx="12" cy="12" r="10" fill="currentColor"></circle>
        `;
    } else {
        voiceBtn.classList.remove('recording');
        // Restore microphone icon
        voiceIcon.innerHTML = `
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
        `;
    }
}

let mediaRecorder = null;
let audioStream = null;

let audioChunks = [];
let processingInterval = null;

async function startBackendVoiceRecording() {
    const voiceBtn = document.getElementById('voice-btn');
    const textarea = document.getElementById('message-input');
    
    try {
        // Request microphone access
        audioStream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        // Update button state
        isRecording = true;
        updateVoiceButton(true);
        voiceBtn.disabled = true;
        audioChunks = [];
        
        // Create MediaRecorder with optimized settings
        mediaRecorder = new MediaRecorder(audioStream, {
            mimeType: 'audio/webm;codecs=opus' // Format mai eficient
        });
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        // Procesează audio-ul periodic pentru feedback mai rapid (doar dacă există chunk-uri noi)
        let lastChunkCount = 0;
        processingInterval = setInterval(async () => {
            if (audioChunks.length > lastChunkCount && mediaRecorder && mediaRecorder.state === 'recording') {
                // Procesează doar chunk-urile noi (ultimele 2-3)
                const newChunks = audioChunks.slice(lastChunkCount);
                if (newChunks.length > 0) {
                    const audioBlob = new Blob(newChunks, { type: 'audio/webm' });
                    lastChunkCount = audioChunks.length;
                    
                    try {
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'recording.webm');
                        
                        const response = await fetch('/api/voice-to-text', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        
                        if (data.success && data.text) {
                            // Adaugă textul la textarea existent
                            const currentText = textarea.value;
                            const newText = data.text.trim();
                            if (newText && !currentText.includes(newText)) {
                                textarea.value = (currentText + ' ' + newText).trim();
                                autoResize(textarea);
                            }
                        }
                    } catch (error) {
                        // Ignoră erorile în procesarea periodică
                        console.log('Processing chunk error (non-critical):', error);
                    }
                }
            }
        }, 3000); // Procesează la fiecare 3 secunde pentru feedback rapid dar fără overload
        
        mediaRecorder.onstop = async () => {
            // Oprește procesarea periodică
            if (processingInterval) {
                clearInterval(processingInterval);
                processingInterval = null;
            }
            
            if (audioStream) {
                audioStream.getTracks().forEach(track => track.stop());
                audioStream = null;
            }
            
            // Procesează tot audio-ul final
            if (audioChunks.length > 0) {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.webm');
                
                try {
                    const response = await fetch('/api/voice-to-text', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success && data.text) {
                        const currentText = textarea.value;
                        // Adaugă doar dacă nu există deja
                        if (!currentText.includes(data.text)) {
                            textarea.value = (currentText + ' ' + data.text).trim();
                            autoResize(textarea);
                        }
                    } else {
                        // Nu afișa alert dacă există deja text procesat
                        if (!textarea.value.trim()) {
                            alert(data.error || 'Nu s-a putut converti audio-ul în text. Te rog încearcă din nou.');
                        }
                    }
                } catch (error) {
                    console.error('Error sending audio to backend:', error);
                    if (!textarea.value.trim()) {
                        alert('Eroare la trimiterea audio-ului. Te rog încearcă din nou.');
                    }
                }
            }
            
            isRecording = false;
            updateVoiceButton(false);
            voiceBtn.disabled = false;
            mediaRecorder = null;
            audioChunks = [];
        };
        
        // Start recording cu timeslice pentru chunk-uri mai mici și mai rapide
        mediaRecorder.start(1000); // Chunk-uri la fiecare secundă
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('Nu s-a putut accesa microfonul. Te rog să permți accesul la microfon.');
        isRecording = false;
        updateVoiceButton(false);
        voiceBtn.disabled = false;
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
            audioStream = null;
        }
        if (processingInterval) {
            clearInterval(processingInterval);
            processingInterval = null;
        }
    }
}

function stopBackendVoiceRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    if (processingInterval) {
        clearInterval(processingInterval);
        processingInterval = null;
    }
}


function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');
    
    if (theme === 'dark') {
        // In dark mode, show sun icon (to switch to light)
        if (sunIcon) sunIcon.style.display = 'block';
        if (moonIcon) moonIcon.style.display = 'none';
    } else {
        // In light mode, show moon icon (to switch to dark)
        if (sunIcon) sunIcon.style.display = 'none';
        if (moonIcon) moonIcon.style.display = 'block';
    }
}

