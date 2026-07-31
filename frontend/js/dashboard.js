// StudyMate AI - Dashboard Module

// Load dashboard data
async function loadDashboard() {
    try {
        await Promise.all([
            loadStats(),
            loadWeakTopics(),
            loadRecentActivity(),
            loadQuizScores()
        ]);
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showToast('Failed to load dashboard data', 'error');
    }
}

// Load statistics
async function loadStats() {
    try {
        const data = await api.get('/api/dashboard');
        
        // Update stats with animation
        animateValue('statStreak', 0, data.streak?.current_streak || 0, 1000);
        animateValue('statQuizzes', 0, data.stats?.quiz_count || 0, 1000);
        animateValue('statNotes', 0, data.stats?.notes_count || 0, 1000);
        animateValue('statFlashcards', 0, data.stats?.flashcard_count || 0, 1000);
        
        // Study time
        const totalMinutes = data.streak?.total_study_minutes || 0;
        const hours = Math.floor(totalMinutes / 60);
        const mins = totalMinutes % 60;
        document.getElementById('statStudyTime').textContent = mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
        
        // Average score
        const avgScore = data.stats?.avg_quiz_score || 0;
        document.getElementById('statAvgScore').textContent = `${avgScore}%`;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Animate counter with GSAP
function animateValue(elementId, start, end, duration) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const obj = { value: start };
    gsap.to(obj, {
        value: end,
        duration: duration / 1000,
        ease: 'power2.out',
        onUpdate: () => {
            element.textContent = Math.round(obj.value);
            element.classList.add('counter-animate');
            setTimeout(() => element.classList.remove('counter-animate'), 500);
        }
    });
}

// Load weak topics
async function loadWeakTopics() {
    try {
        const data = await api.get('/api/dashboard');
        const weakTopics = data.weak_topics || [];
        const container = document.getElementById('weakTopics');
        
        if (weakTopics.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: 30px 20px;">
                    <p style="font-size: 0.9rem;">Complete quizzes to identify weak areas</p>
                </div>
            `;
            return;
        }

        container.innerHTML = weakTopics.map(topic => `
            <div class="activity-item">
                <div class="activity-icon">⚠️</div>
                <div style="flex: 1;">
                    <div style="color: #fff; font-weight: 500; font-size: 0.9rem;">${escapeHtml(topic.content)}</div>
                    <div style="color: var(--text2); font-size: 0.8rem; margin-top: 2px;">Importance: ${'⭐'.repeat(topic.importance || 1)}</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load weak topics:', error);
    }
}

// Load recent activity
async function loadRecentActivity() {
    try {
        const data = await api.get('/api/dashboard');
        const activities = data.recent_activity || [];
        const container = document.getElementById('recentActivity');
        
        if (activities.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: 30px 20px;">
                    <p style="font-size: 0.9rem;">No activity yet. Start studying!</p>
                </div>
            `;
            return;
        }

        const icons = {
            'chat': '💬',
            'quiz': '❓',
            'flashcard': '🃏',
            'notes': '📝',
            'study': '📚'
        };

        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">${icons[activity.activity_type] || '📌'}</div>
                <div style="flex: 1;">
                    <div style="color: #fff; font-weight: 500; font-size: 0.9rem;">${escapeHtml(activity.description || 'Activity')}</div>
                    <div style="color: var(--text2); font-size: 0.8rem; margin-top: 2px;">${formatRelative(activity.created_at)}</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load recent activity:', error);
    }
}

// Load quiz scores
async function loadQuizScores() {
    try {
        const data = await api.get('/api/dashboard');
        const quizScores = data.quiz_scores || [];
        const container = document.getElementById('quizScores');
        
        if (quizScores.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: 30px 20px;">
                    <p style="font-size: 0.9rem;">No quizzes taken yet</p>
                </div>
            `;
            return;
        }

        container.innerHTML = quizScores.slice(0, 5).map(quiz => {
            const percentage = Math.round((quiz.score / quiz.total) * 100);
            const color = percentage >= 80 ? 'var(--success)' : percentage >= 60 ? 'var(--warning)' : 'var(--danger)';
            
            return `
                <div class="activity-item">
                    <div class="activity-icon">📝</div>
                    <div style="flex: 1;">
                        <div style="color: #fff; font-weight: 500; font-size: 0.9rem;">${escapeHtml(quiz.title || 'Quiz')}</div>
                        <div style="color: var(--text2); font-size: 0.8rem; margin-top: 2px;">
                            Score: <span style="color: ${color}; font-weight: 600;">${quiz.score}/${quiz.total} (${percentage}%)</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load quiz scores:', error);
    }
}

// Escape HTML helper
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}