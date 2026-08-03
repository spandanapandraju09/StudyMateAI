// AIRA AI OS — Universal Chat Module
let currentSessionId = null;
let isStreaming = false;
let allSessions = [];
let activeCategory = 'all';
let isMultiSelect = false;
let selectedSessions = new Set();
let recognition = null;
let isRecording = false;

document.addEventListener('DOMContentLoaded', () => {
    loadSessions();
    setupUrlPrompt();
    initSpeechRecognition();
});

function setupUrlPrompt() {
    const params = new URLSearchParams(window.location.search);
    const initialPrompt = params.get('prompt');
    if (initialPrompt) {
        document.getElementById('prompt').value = initialPrompt;
    }
}

// Voice Input (Web Speech API)
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');
            document.getElementById('prompt').value = transcript;
        };
        recognition.onend = () => {
            isRecording = false;
            const btn = document.getElementById('voiceBtn');
            if (btn) btn.style.background = '';
        };
    }
}

function toggleVoiceInput() {
    if (!recognition) {
        showToast('Speech recognition not supported in this browser.', 'error');
        return;
    }
    const btn = document.getElementById('voiceBtn');
    if (isRecording) {
        recognition.stop();
        isRecording = false;
        if (btn) btn.style.background = '';
    } else {
        recognition.start();
        isRecording = true;
        if (btn) btn.style.background = 'rgba(239,68,68,0.3)';
        showToast('Listening... Speak now 🎙️', 'success');
    }
}

// Load all sessions
async function loadSessions() {
    try {
        const query = document.getElementById('searchChatsInput')?.value || '';
        allSessions = await api.get(`/api/chat/sessions${query ? '?q=' + encodeURIComponent(query) : ''}`);
        renderSessionList(allSessions);
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

function renderSessionList(sessions) {
    const sessionList = document.getElementById('sessionList');
    if (!sessionList) return;

    let filtered = sessions;
    if (activeCategory === 'pinned') filtered = sessions.filter(s => s.is_pinned);
    else if (activeCategory === 'favorites') filtered = sessions.filter(s => s.is_favorite);
    else if (activeCategory === 'archived') filtered = sessions.filter(s => s.is_archived);
    else filtered = sessions.filter(s => !s.is_archived);

    if (filtered.length === 0) {
        sessionList.innerHTML = '<div class="empty-state" style="padding:16px"><p style="font-size:.8rem; color:var(--text2);">No conversations found</p></div>';
        return;
    }

    sessionList.innerHTML = filtered.map(s => `
        <div class="session-item ${s.id === currentSessionId ? 'active' : ''} ${s.is_pinned ? 'pinned-chat' : ''}" onclick="${isMultiSelect ? `toggleSelectSession(${s.id})` : `loadSession(${s.id})`}" style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; border-radius:10px; margin-bottom:4px; cursor:pointer; background:${selectedSessions.has(s.id) ? 'rgba(239,68,68,0.2)' : (s.id === currentSessionId ? 'rgba(0,240,255,0.15)' : 'rgba(255,255,255,0.03)')}; border:1px solid ${s.id === currentSessionId ? 'var(--accent)' : 'transparent'};">
            <div style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:flex; align-items:center; gap:6px;">
                ${isMultiSelect ? `<input type="checkbox" ${selectedSessions.has(s.id) ? 'checked' : ''} onclick="event.stopPropagation(); toggleSelectSession(${s.id})">` : ''}
                <span>${s.is_pinned ? '📌' : (s.is_favorite ? '⭐' : '💬')}</span>
                <span class="session-title" style="color:#fff; font-size:0.84rem; font-weight:500;">${escapeHtml(s.title || 'New Chat')}</span>
            </div>
            ${!isMultiSelect ? `
            <div class="session-actions" onclick="event.stopPropagation()" style="display:flex; gap:4px; opacity:0.8;">
                <button title="${s.is_pinned ? 'Unpin' : 'Pin'}" onclick="togglePinSession(${s.id}, ${!s.is_pinned})" style="background:none; border:none; color:#fff; cursor:pointer; font-size:0.75rem;">${s.is_pinned ? '📌' : '📍'}</button>
                <button title="${s.is_favorite ? 'Unfavorite' : 'Favorite'}" onclick="toggleFavoriteSession(${s.id}, ${!s.is_favorite})" style="background:none; border:none; color:#fff; cursor:pointer; font-size:0.75rem;">${s.is_favorite ? '⭐' : '☆'}</button>
                <button title="Rename" onclick="renameSessionPrompt(${s.id}, '${escapeHtml(s.title)}')" style="background:none; border:none; color:#fff; cursor:pointer; font-size:0.75rem;">✏️</button>
                <button title="Delete" onclick="deleteSession(${s.id})" style="background:none; border:none; color:var(--danger); cursor:pointer; font-size:0.75rem;">✕</button>
            </div>
            ` : ''}
        </div>
    `).join('');
}

// Multi Select Mode
function toggleMultiSelectMode() {
    isMultiSelect = !isMultiSelect;
    selectedSessions.clear();
    const bar = document.getElementById('multiDeleteBar');
    if (bar) bar.style.display = isMultiSelect ? 'flex' : 'none';
    renderSessionList(allSessions);
}

function toggleSelectSession(id) {
    if (selectedSessions.has(id)) selectedSessions.delete(id);
    else selectedSessions.add(id);
    const countText = document.getElementById('selectedCountText');
    if (countText) countText.textContent = `${selectedSessions.size} selected`;
    renderSessionList(allSessions);
}

async function executeBatchDelete() {
    if (selectedSessions.size === 0) return;
    if (!confirm(`Delete ${selectedSessions.size} selected chats?`)) return;
    try {
        await api.post('/api/chat/sessions/batch-delete', { session_ids: Array.from(selectedSessions) });
        showToast('Selected chats deleted', 'success');
        isMultiSelect = false;
        document.getElementById('multiDeleteBar').style.display = 'none';
        selectedSessions.clear();
        loadSessions();
    } catch (e) {
        showToast('Failed to delete selected chats', 'error');
    }
}

// Create new chat session
async function createNewSession() {
    try {
        const result = await api.post('/api/chat/sessions', { title: 'New Conversation' });
        currentSessionId = result.id;
        document.getElementById('chatTitle').textContent = 'New Conversation';
        document.getElementById('chatMessages').innerHTML = `
            <div class="empty-state">
                <div class="es-icon">✨</div>
                <h3>AIRA AI Operating System</h3>
                <p>Ask anything: Coding, Writing, Translation, Business Strategy, Research & Daily Tasks</p>
            </div>
        `;
        loadSessions();
        showToast('New AIRA chat session created', 'success');
    } catch (error) {
        showToast('Failed to create session: ' + error.message, 'error');
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
                    <div class="es-icon">✨</div>
                    <h3>AIRA AI Operating System</h3>
                    <p>Ask anything: Coding, Writing, Translation, Business Strategy, Research & Daily Tasks</p>
                </div>
            `;
        } else {
            chatMessages.innerHTML = messages.map(msg => createMessageHtml(msg.role, msg.content)).join('');
        }
        
        const sess = allSessions.find(s => s.id === sessionId);
        if (sess) document.getElementById('chatTitle').textContent = sess.title || 'Conversation';
        
        loadSessions();
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        showToast('Failed to load session: ' + error.message, 'error');
    }
}

// Toggle Pin
async function togglePinSession(id, isPinned) {
    try {
        await api.put(`/api/chat/sessions/${id}`, { is_pinned: isPinned });
        loadSessions();
        showToast(isPinned ? 'Chat pinned to top' : 'Chat unpinned', 'success');
    } catch (e) {
        showToast('Failed to update pin', 'error');
    }
}

// Toggle Favorite
async function toggleFavoriteSession(id, isFav) {
    try {
        await api.put(`/api/chat/sessions/${id}`, { is_favorite: isFav });
        loadSessions();
        showToast(isFav ? 'Added to Favorites' : 'Removed from Favorites', 'success');
    } catch (e) {
        showToast('Failed to update favorite', 'error');
    }
}

// Rename Session
async function renameSessionPrompt(id, oldTitle) {
    const newTitle = prompt('Rename Chat Session:', oldTitle);
    if (!newTitle || newTitle.trim() === oldTitle) return;
    try {
        await api.put(`/api/chat/sessions/${id}`, { title: newTitle.trim() });
        loadSessions();
        if (currentSessionId === id) document.getElementById('chatTitle').textContent = newTitle.trim();
        showToast('Chat renamed', 'success');
    } catch (e) {
        showToast('Failed to rename session', 'error');
    }
}

// Voice Input Dictation Engine
let speechRecognition = null;
let isDictating = false;

function toggleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        showToast('Voice dictation is not supported in this browser. Try Chrome/Edge.', 'error');
        return;
    }

    const voiceBtn = document.getElementById('voiceBtn');

    if (isDictating && speechRecognition) {
        speechRecognition.stop();
        isDictating = false;
        if (voiceBtn) voiceBtn.style.color = '#fff';
        showToast('Voice dictation stopped', 'info');
        return;
    }

    try {
        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = true;
        speechRecognition.lang = 'en-US';

        speechRecognition.onstart = () => {
            isDictating = true;
            if (voiceBtn) voiceBtn.style.color = '#f43f5e';
            showToast('🎙️ Listening... Speak into your microphone', 'success');
        };

        speechRecognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                transcript += event.results[i][0].transcript;
            }
            const promptEl = document.getElementById('prompt');
            if (promptEl) promptEl.value = transcript;
        };

        speechRecognition.onerror = (event) => {
            isDictating = false;
            if (voiceBtn) voiceBtn.style.color = '#fff';
            showToast('Speech recognition notice: ' + (event.error || 'Stopped'), 'error');
        };

        speechRecognition.onend = () => {
            isDictating = false;
            if (voiceBtn) voiceBtn.style.color = '#fff';
        };

        speechRecognition.start();
    } catch (err) {
        console.error('Speech recognition error:', err);
        showToast('Could not start speech recognition', 'error');
    }
}

// Export Session Engine
async function exportSession(id) {
    const targetId = id || currentSessionId;
    if (!targetId) {
        showToast('Select a conversation to export', 'error');
        return;
    }

    try {
        let markdownText = '';
        try {
            const data = await api.get(`/api/chat/sessions/${targetId}/export`);
            markdownText = data.markdown;
        } catch (err) {
            const messages = await api.get(`/api/chat/sessions/${targetId}/messages`);
            markdownText = `# Nexus AI Chat Export (Session #${targetId})\n*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;
            messages.forEach(msg => {
                const roleLabel = msg.role === 'user' ? '👤 User' : '✨ Nexus AI';
                markdownText += `### ${roleLabel}\n${msg.content}\n\n`;
            });
        }

        const blob = new Blob([markdownText], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Nexus_AI_Chat_${targetId}.md`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Chat exported to Markdown file!', 'success');
    } catch (e) {
        console.error('Export failed:', e);
        showToast('Failed to export conversation', 'error');
    }
}

function exportCurrentSession() {
    exportSession(currentSessionId);
}

// Import Chat JSON
function importChatJSON() {
    document.getElementById('importChatFile').click();
}

async function handleImportChatFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    try {
        const text = await file.text();
        const json = JSON.parse(text);
        const title = json.title || file.name.replace('.json', '');
        const msgs = json.messages || [];
        await api.post('/api/chat/sessions/import', { title, messages: msgs });
        showToast('Chat imported successfully!', 'success');
        loadSessions();
    } catch (e) {
        showToast('Failed to import chat JSON', 'error');
    }
}

// Delete Session
async function deleteSession(sessionId) {
    if (!confirm('Delete this conversation?')) return;
    try {
        await api.delete(`/api/chat/sessions/${sessionId}`);
        if (currentSessionId === sessionId) {
            currentSessionId = null;
            document.getElementById('chatMessages').innerHTML = `
                <div class="empty-state">
                    <div class="es-icon">✨</div>
                    <h3>AIRA AI Operating System</h3>
                    <p>Ask anything: Coding, Writing, Translation, Business Strategy, Research & Daily Tasks</p>
                </div>
            `;
            document.getElementById('chatTitle').textContent = 'New Conversation';
        }
        loadSessions();
        showToast('Chat deleted', 'success');
    } catch (error) {
        showToast('Failed to delete: ' + error.message, 'error');
    }
}

// Clear All Sessions
async function clearAllSessions() {
    if (!confirm('Clear ALL conversation history?')) return;
    try {
        await api.delete('/api/chat/sessions');
        currentSessionId = null;
        document.getElementById('chatMessages').innerHTML = `
            <div class="empty-state">
                <div class="es-icon">✨</div>
                <h3>AIRA AI Operating System</h3>
                <p>Ask anything: Coding, Writing, Translation, Business Strategy, Research & Daily Tasks</p>
            </div>
        `;
        document.getElementById('chatTitle').textContent = 'New Conversation';
        loadSessions();
        showToast('All chat sessions cleared', 'success');
    } catch (error) {
        showToast('Failed to clear sessions', 'error');
    }
}

// Filter Category
function setCategoryFilter(cat) {
    activeCategory = cat;
    document.querySelectorAll('.cat-filter-btn').forEach(btn => btn.classList.remove('active', 'btn-primary'));
    event.target.classList.add('active', 'btn-primary');
    renderSessionList(allSessions);
}

// Search Chats
function filterChatHistory() {
    loadSessions();
}

// Send Message
async function sendMessage() {
    const prompt = document.getElementById('prompt');
    const message = prompt.value.trim();
    if (!message || isStreaming) return;

    const chatMessages = document.getElementById('chatMessages');
    const emptyState = chatMessages.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    chatMessages.innerHTML += createMessageHtml('user', message);
    prompt.value = '';
    prompt.style.height = 'auto';
    chatMessages.scrollTop = chatMessages.scrollHeight;

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
    if (sendBtn) sendBtn.disabled = true;

    window.dispatchEvent(new Event('robot:thinking'));

    try {
        const result = await api.post('/api/chat/send', {
            message: message,
            session_id: currentSessionId
        });

        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        const aiMsgHtml = createMessageHtml('assistant', result.reply);
        chatMessages.insertAdjacentHTML('beforeend', aiMsgHtml);
        currentSessionId = result.session_id;

        window.dispatchEvent(new Event('robot:talking'));

        const titleEl = document.getElementById('chatTitle');
        if (titleEl && titleEl.textContent === 'New Conversation') {
            titleEl.textContent = message.substring(0, 36) + (message.length > 36 ? '...' : '');
        }

        loadSessions();
    } catch (error) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        chatMessages.innerHTML += createMessageHtml('assistant', '⚠️ AIRA AI encountered an error processing your query. Please try again.');
        showToast('Failed to send message: ' + error.message, 'error');
    } finally {
        isStreaming = false;
        if (sendBtn) sendBtn.disabled = false;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function sendQuickPrompt(promptText) {
    document.getElementById('prompt').value = promptText;
    sendMessage();
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function createMessageHtml(role, content) {
    const isUser = role === 'user';
    const formattedContent = formatMessage(content);
    return `
        <div class="message ${isUser ? 'user-message chat-bubble-user' : 'ai-message chat-bubble-ai'}" style="margin-bottom:16px;">
            ${formattedContent}
        </div>
    `;
}

function formatMessage(text) {
    if (!text) return '';
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}