// StudyMate AI - Chat Module
let currentSessionId = null;
let isStreaming = false;

// Load sessions on init
document.addEventListener('DOMContentLoaded', () => {
    loadSessions();
});

// Create new chat session
async function createNewSession() {
    try {
        const result = await api.post('/api/chat/sessions');
        currentSessionId = result.id;
        document.getElementById('chatTitle').textContent = 'New Chat';
        document.getElementById('chatMessages').innerHTML = `
            <div class="empty-state">
                <div class="es-icon">💬</div>
                <h3>Start a Conversation</h3>
                <p>Ask me anything about your studies, or just chat!</p>
            </div>
        `;
        loadSessions();
        showToast('New chat created', 'success');
    } catch (error) {
        showToast('Failed to create session: ' + error.message, 'error');
    }
}

// Load all sessions
async function loadSessions() {
    try {
        const sessions = await api.get('/api/chat/sessions');
        const sessionList = document.getElementById('sessionList');
        
        if (sessions.length === 0) {
            sessionList.innerHTML = '<div class="empty-state" style="padding:20px"><p style="font-size:.85rem">No chats yet</p></div>';
            return;
        }

        sessionList.innerHTML = sessions.map(s => `
            <div class="session-item ${s.id === currentSessionId ? 'active' : ''}" onclick="loadSession(${s.id})">
                <span class="session-title">${escapeHtml(s.title || 'New Chat')}</span>
                <button class="session-del" onclick="event.stopPropagation(); deleteSession(${s.id})">✕</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

// Load specific session
async function loadSession(sessionId) {
    try {
        currentSessionId = sessionId;
        const messages = await api.get(`/api/chat/sessions/${sessionId}/messages`);
        const chatMessages = document.getElementById('chatMessages');
        
        if (messages.length === 0) {
            chatMessages.innerHTML = `
                <div class="empty-state">
                    <div class="es-icon">💬</div>
                    <h3>Start a Conversation</h3>
                    <p>Ask me anything about your studies, or just chat!</p>
                </div>
            `;
        } else {
            chatMessages.innerHTML = messages.map(msg => createMessageHtml(msg.role, msg.content)).join('');
        }
        
        loadSessions();
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        showToast('Failed to load session: ' + error.message, 'error');
    }
}

// Delete session
async function deleteSession(sessionId) {
    if (!confirm('Delete this chat?')) return;
    
    try {
        await api.delete(`/api/chat/sessions/${sessionId}`);
        if (currentSessionId === sessionId) {
            currentSessionId = null;
            document.getElementById('chatMessages').innerHTML = `
                <div class="empty-state">
                    <div class="es-icon">💬</div>
                    <h3>Start a Conversation</h3>
                    <p>Ask me anything about your studies, or just chat!</p>
                </div>
            `;
            document.getElementById('chatTitle').textContent = 'New Chat';
        }
        loadSessions();
        showToast('Chat deleted', 'success');
    } catch (error) {
        showToast('Failed to delete: ' + error.message, 'error');
    }
}

// Send message
async function sendMessage() {
    const prompt = document.getElementById('prompt');
    const message = prompt.value.trim();
    
    if (!message || isStreaming) return;

    // Clear empty state if present
    const chatMessages = document.getElementById('chatMessages');
    const emptyState = chatMessages.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    // Add user message
    chatMessages.innerHTML += createMessageHtml('user', message);
    prompt.value = '';
    prompt.style.height = 'auto';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Show typing indicator with premium animation
    const typingId = 'typing-' + Date.now();
    chatMessages.insertAdjacentHTML('beforeend', `
        <div class="message ai-message chat-bubble-ai" id="${typingId}">
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>
    `);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    isStreaming = true;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    try {
        const result = await api.post('/api/chat/send', {
            message: message,
            session_id: currentSessionId
        });

        // Remove typing indicator
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        // Add AI response with animation
        const aiMsgHtml = createMessageHtml('assistant', result.reply);
        chatMessages.insertAdjacentHTML('beforeend', aiMsgHtml);
        currentSessionId = result.session_id;
        
        // Update chat title if it's the first message
        const titleEl = document.getElementById('chatTitle');
        if (titleEl.textContent === 'New Chat') {
            titleEl.textContent = message.substring(0, 40) + (message.length > 40 ? '...' : '');
        }
        
        loadSessions();
    } catch (error) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        chatMessages.innerHTML += createMessageHtml('assistant', '⚠️ Sorry, I encountered an error. Please try again.');
        showToast('Failed to send message: ' + error.message, 'error');
    } finally {
        isStreaming = false;
        sendBtn.disabled = false;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Send quick prompt
function sendQuickPrompt(prompt) {
    document.getElementById('prompt').value = prompt;
    sendMessage();
}

// Handle Enter key
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Create message HTML
function createMessageHtml(role, content) {
    const isUser = role === 'user';
    const formattedContent = formatMessage(content);
    return `
        <div class="message ${isUser ? 'user-message' : 'ai-message'} ${isUser ? 'chat-bubble-user' : 'chat-bubble-ai'}">
            ${formattedContent}
        </div>
    `;
}

// Format message with basic markdown support
function formatMessage(text) {
    if (!text) return '';
    
    // Escape HTML
    let formatted = escapeHtml(text);
    
    // Code blocks
    formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
    
    // Inline code
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Bold
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}