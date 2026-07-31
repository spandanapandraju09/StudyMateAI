// StudyMate AI - Notes Module

// Load notes on init
document.addEventListener('DOMContentLoaded', () => {
    // Notes functionality is initialized in notes.html
});

// Search notes (client-side filtering)
function searchNotes() {
    const query = document.getElementById('searchNotes').value.toLowerCase();
    const cards = document.querySelectorAll('.note-card');
    
    cards.forEach(card => {
        const title = card.querySelector('h4').textContent.toLowerCase();
        const content = card.querySelector('p').textContent.toLowerCase();
        card.style.display = (title.includes(query) || content.includes(query)) ? 'block' : 'none';
    });
}

// Get file icon based on type
function getFileIcon(fileType) {
    const icons = {
        'pdf': '📕',
        'docx': '📘',
        'doc': '📘',
        'txt': '📄',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️'
    };
    return icons[fileType?.toLowerCase()] || '📄';
}

// Open note in modal
async function openNote(noteId) {
    try {
        currentNoteId = noteId;
        const note = await api.get(`/api/notes/${noteId}`);
        
        document.getElementById('modalNoteTitle').textContent = note.title;
        document.getElementById('modalNoteContent').textContent = note.content;
        document.getElementById('noteModal').style.display = 'flex';
    } catch (error) {
        showToast('Failed to load note: ' + error.message, 'error');
    }
}

// Close note modal
function closeNoteModal() {
    document.getElementById('noteModal').style.display = 'none';
    currentNoteId = null;
}

// Delete current note
async function deleteCurrentNote() {
    if (!currentNoteId) return;
    if (!confirm('Delete this note?')) return;

    try {
        await api.delete(`/api/notes/${currentNoteId}`);
        showToast('Note deleted', 'success');
        closeNoteModal();
        loadNotes();
    } catch (error) {
        showToast('Failed to delete: ' + error.message, 'error');
    }
}

// Generate quiz from note
async function generateQuizFromNote() {
    if (!currentNoteId) return;
    showToast('Redirecting to Quiz page...', 'success');
    setTimeout(() => {
        window.location.href = `/quiz.html?material_id=${currentNoteId}`;
    }, 500);
}

// Generate flashcards from note
async function generateFlashcardsFromNote() {
    if (!currentNoteId) return;
    showToast('Redirecting to Flashcards page...', 'success');
    setTimeout(() => {
        window.location.href = `/flashcards.html?material_id=${currentNoteId}`;
    }, 500);
}

// Toggle mobile sidebar
function toggleMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}