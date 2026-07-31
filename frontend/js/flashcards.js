// StudyMate AI - Flashcards Module

let cards = [];
let currentIndex = 0;

document.addEventListener('DOMContentLoaded', () => {
    loadCards();
});

async function loadCards() {
    try {
        cards = await api.get('/api/flashcards');
        currentIndex = 0;
        renderCard();
    } catch (err) {
        console.error('Failed to load flashcards:', err);
    }
}

async function generateFlashcards() {
    try {
        showToast('Generating flashcards...', 'success');
        const res = await api.post('/api/flashcards/generate', { count: 10 });
        cards = res.cards || [];
        currentIndex = 0;
        renderCard();
        showToast(`Generated ${cards.length} cards!`, 'success');
    } catch (err) {
        showToast(err.message || 'Failed to generate flashcards', 'error');
    }
}

function renderCard() {
    const deck = document.getElementById('flashcardDeck');
    const controls = document.getElementById('deckControls');
    const progress = document.getElementById('cardProgress');

    if (!cards || cards.length === 0) {
        deck.innerHTML = `
            <div class="empty-state" style="padding: 40px 20px;">
                <div class="es-icon">🃏</div>
                <h3>No Flashcards Available</h3>
                <p>Click "Generate Cards" to create flashcards from your notes</p>
            </div>
        `;
        controls.style.display = 'none';
        return;
    }

    controls.style.display = 'flex';
    progress.textContent = `${currentIndex + 1} / ${cards.length}`;

    const card = cards[currentIndex];
    deck.innerHTML = `
        <div class="flashcard-card-wrap" onclick="toggleCardFlip(this)" style="
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--border);
            border-radius: 20px;
            min-height: 250px;
            padding: 30px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            cursor: pointer;
            transition: transform 0.3s, background 0.3s;
            position: relative;
        ">
            <div class="fc-side fc-front">
                <div style="font-size: 0.8rem; color: var(--accent); margin-bottom: 12px; font-weight: 600;">FRONT (Click to Flip)</div>
                <div style="font-size: 1.15rem; color: #fff; font-weight: 500;">${escapeHtml(card.front)}</div>
            </div>
            <div class="fc-side fc-back" style="display: none;">
                <div style="font-size: 0.8rem; color: var(--success); margin-bottom: 12px; font-weight: 600;">BACK (Answer)</div>
                <div style="font-size: 1.05rem; color: #e2e8f0; line-height: 1.6;">${escapeHtml(card.back)}</div>
            </div>
            <div style="position: absolute; bottom: 16px; display: flex; gap: 10px;" onclick="event.stopPropagation()">
                <button class="btn btn-ghost btn-sm" onclick="markCardStatus(${card.id}, 'unknown')">❌ Still Learning</button>
                <button class="btn btn-ghost btn-sm" onclick="markCardStatus(${card.id}, 'known')">✅ Mastered</button>
            </div>
        </div>
    `;
}

function toggleCardFlip(el) {
    const front = el.querySelector('.fc-front');
    const back = el.querySelector('.fc-back');
    if (front.style.display === 'none') {
        front.style.display = 'block';
        back.style.display = 'none';
    } else {
        front.style.display = 'none';
        back.style.display = 'block';
    }
}

async function markCardStatus(id, status) {
    try {
        await api.put(`/api/flashcards/${id}/status`, { status });
        showToast(status === 'known' ? 'Marked as Mastered! 🎉' : 'Saved for review', 'success');
        nextCard();
    } catch (err) {
        showToast('Failed to update status: ' + err.message, 'error');
    }
}

function prevCard() {
    if (currentIndex > 0) {
        currentIndex--;
        renderCard();
    }
}

function nextCard() {
    if (currentIndex < cards.length - 1) {
        currentIndex++;
        renderCard();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}
