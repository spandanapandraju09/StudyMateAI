// StudyMate AI - Quiz Module

// Load notes list on init
document.addEventListener('DOMContentLoaded', () => {
    loadNotesList();
});

// Toggle between notes and custom topic
function toggleQuizSource() {
    const source = document.getElementById('quizSource').value;
    document.getElementById('notesSelect').style.display = source === 'notes' ? 'block' : 'none';
    document.getElementById('customTopic').style.display = source === 'custom' ? 'block' : 'none';
}

// Load notes for quiz generation
async function loadNotesList() {
    try {
        const notes = await api.get('/api/notes');
        const select = document.getElementById('notesList');
        
        if (notes.length === 0) {
            select.innerHTML = '<option value="">No notes available</option>';
            return;
        }

        select.innerHTML = notes.map(note => 
            `<option value="${note.id}">${escapeHtml(note.title)}</option>`
        ).join('');
    } catch (error) {
        console.error('Failed to load notes:', error);
    }
}

// Generate quiz
async function generateQuiz() {
    const source = document.getElementById('quizSource').value;
    const quizType = document.getElementById('quizType').value;
    const count = parseInt(document.getElementById('questionSlider').value);

    let materialId = null;
    let content = '';

    if (source === 'notes') {
        materialId = document.getElementById('notesList').value;
        if (!materialId) {
            showToast('Please select notes', 'error');
            return;
        }
    } else {
        content = document.getElementById('quizTopic').value.trim();
        if (!content) {
            showToast('Please enter a topic or content', 'error');
            return;
        }
    }

    try {
        showToast('Generating quiz...', 'success');
        
        const requestBody = {
            quiz_type: quizType,
            count: count
        };
        
        if (materialId) {
            requestBody.material_id = parseInt(materialId);
        } else {
            requestBody.content = content;
        }

        const result = await api.post('/api/quiz/generate', requestBody);
        
        currentQuiz = result;
        currentQuestionIndex = 0;
        userAnswers = {};
        
        // Setup quiz UI
        document.getElementById('quizTitle').textContent = result.title;
        document.getElementById('totalQuestions').textContent = result.questions.length;
        document.getElementById('quizSetup').style.display = 'none';
        document.getElementById('quizInterface').style.display = 'block';
        document.getElementById('quizResults').style.display = 'none';
        
        // Start timer
        quizStartTime = Date.now();
        startTimer();
        
        // Load first question
        loadQuestion();
        
        showToast('Quiz generated!', 'success');
    } catch (error) {
        showToast('Failed to generate quiz: ' + error.message, 'error');
    }
}

// Start quiz timer
function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - quizStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        document.getElementById('quizTimer').textContent = `${minutes}:${seconds}`;
    }, 1000);
}

// Load current question
function loadQuestion() {
    if (!currentQuiz || !currentQuiz.questions[currentQuestionIndex]) return;
    
    const question = currentQuiz.questions[currentQuestionIndex];
    const total = currentQuiz.questions.length;
    
    // Update UI
    document.getElementById('currentQuestion').textContent = currentQuestionIndex + 1;
    document.getElementById('questionText').textContent = question.question;
    
    // Update progress bar
    const progress = ((currentQuestionIndex + 1) / total) * 100;
    document.getElementById('quizProgress').style.width = `${progress}%`;
    
    // Render options
    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = '';
    
    if (question.options && question.options.length > 0) {
        // Multiple choice
        question.options.forEach((option, index) => {
            const isSelected = userAnswers[question.id] === option;
            const optionDiv = document.createElement('div');
            optionDiv.className = `quiz-option ${isSelected ? 'selected' : ''}`;
            optionDiv.textContent = option;
            optionDiv.onclick = () => selectAnswer(question.id, option);
            optionsContainer.appendChild(optionDiv);
        });
    } else {
        // Short answer
        const textarea = document.createElement('textarea');
        textarea.id = 'shortAnswerInput';
        textarea.placeholder = 'Type your answer here...';
        textarea.rows = 4;
        textarea.style.cssText = 'width: 100%; padding: 12px; background: rgba(255,255,255,.05); border: 1px solid var(--border); border-radius: var(--r2); color: var(--text); font-family: var(--font); resize: vertical;';
        textarea.value = userAnswers[question.id] || '';
        textarea.oninput = (e) => selectAnswer(question.id, e.target.value);
        optionsContainer.appendChild(textarea);
    }
    
    // Update buttons
    document.getElementById('prevBtn').disabled = currentQuestionIndex === 0;
    
    if (currentQuestionIndex === total - 1) {
        document.getElementById('nextBtn').style.display = 'none';
        document.getElementById('submitBtn').style.display = 'inline-flex';
    } else {
        document.getElementById('nextBtn').style.display = 'inline-flex';
        document.getElementById('submitBtn').style.display = 'none';
    }
}

// Select answer
function selectAnswer(questionId, answer) {
    userAnswers[questionId] = answer;
    
    // Update UI for MCQ
    if (currentQuiz.questions[currentQuestionIndex].options) {
        const options = document.querySelectorAll('.quiz-option');
        options.forEach(opt => {
            opt.classList.toggle('selected', opt.textContent === answer);
        });
    }
}

// Next question
function nextQuestion() {
    if (currentQuestionIndex < currentQuiz.questions.length - 1) {
        currentQuestionIndex++;
        loadQuestion();
    }
}

// Previous question
function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        loadQuestion();
    }
}

// Submit quiz
async function submitQuiz() {
    if (!confirm('Submit quiz? You cannot change answers after submission.')) return;
    
    try {
        clearInterval(timerInterval);
        
        const timeTaken = Math.floor((Date.now() - quizStartTime) / 1000);
        
        const result = await api.post(`/api/quiz/${currentQuiz.id}/submit`, {
            answers: userAnswers
        });
        
        // Show results
        showResults(result, timeTaken);
    } catch (error) {
        showToast('Failed to submit quiz: ' + error.message, 'error');
    }
}

// Show quiz results
function showResults(result, timeTaken) {
    document.getElementById('quizInterface').style.display = 'none';
    document.getElementById('quizResults').style.display = 'block';
    
    const percentage = result.percentage;
    const scoreRing = document.getElementById('scoreRing');
    const scoreText = document.getElementById('scoreText');
    
    // Animate score ring
    setTimeout(() => {
        scoreRing.style.setProperty('--pct', percentage);
    }, 100);
    
    scoreText.textContent = `${percentage}%`;
    
    // Result message
    let title, message;
    if (percentage >= 90) {
        title = '🏆 Outstanding!';
        message = 'You\'re a master of this topic!';
    } else if (percentage >= 80) {
        title = '🌟 Excellent!';
        message = 'Great job! You really know your stuff!';
    } else if (percentage >= 70) {
        title = '👍 Good Work!';
        message = 'You\'re doing well! Keep it up!';
    } else if (percentage >= 60) {
        title = '📚 Not Bad!';
        message = 'You passed! Review the topics you missed.';
    } else {
        title = '💪 Keep Practicing!';
        message = 'Don\'t give up! Review and try again.';
    }
    
    document.getElementById('resultTitle').textContent = title;
    document.getElementById('resultMessage').textContent = `${message} You scored ${result.score}/${result.total}`;
    
    // Store results for review
    window.quizResults = result;
}

// View answers
function viewAnswers() {
    const container = document.getElementById('answersContainer');
    const reviewDiv = document.getElementById('answersReview');
    
    if (!window.quizResults) return;
    
    container.innerHTML = window.quizResults.results.map((result, index) => {
        const question = currentQuiz.questions[index];
        const icon = result.correct ? '✅' : '❌';
        const color = result.correct ? 'var(--success)' : 'var(--danger)';
        
        return `
            <div class="activity-item" style="margin-bottom: 16px; padding: 16px; background: rgba(255,255,255,.03); border-radius: var(--r2);">
                <div style="color: #fff; font-weight: 600; margin-bottom: 8px;">${icon} Question ${index + 1}</div>
                <div style="color: var(--text); margin-bottom: 12px;">${escapeHtml(question.question)}</div>
                ${question.options ? `
                    <div style="color: var(--text2); font-size: 0.9rem; margin-bottom: 4px;">
                        Your answer: <span style="color: ${result.correct ? 'var(--success)' : 'var(--danger)'}">${escapeHtml(userAnswers[question.id] || 'No answer')}</span>
                    </div>
                    ${!result.correct ? `
                        <div style="color: var(--success); font-size: 0.9rem; margin-bottom: 4px;">
                            Correct answer: ${escapeHtml(result.correct_answer)}
                        </div>
                    ` : ''}
                ` : `
                    <div style="color: var(--text2); font-size: 0.9rem; margin-bottom: 4px;">
                        Your answer: ${escapeHtml(userAnswers[question.id] || 'No answer')}
                    </div>
                    ${result.explanation ? `
                        <div style="color: var(--accent); font-size: 0.85rem; margin-top: 8px; padding: 8px; background: rgba(0,229,255,.05); border-radius: var(--r2);">
                            💡 ${escapeHtml(result.explanation)}
                        </div>
                    ` : ''}
                `}
            </div>
        `;
    }).join('');
    
    reviewDiv.style.display = 'block';
    reviewDiv.scrollIntoView({ behavior: 'smooth' });
}

// Retry wrong questions
function retryWrongQuestions() {
    if (!window.quizResults) return;
    
    const wrongQuestions = window.quizResults.results
        .map((result, index) => ({ ...result, question: currentQuiz.questions[index] }))
        .filter(result => !result.correct);
    
    if (wrongQuestions.length === 0) {
        showToast('You got all questions correct! 🎉', 'success');
        return;
    }
    
    // Create new quiz with wrong questions
    currentQuiz = {
        id: currentQuiz.id,
        title: currentQuiz.title + ' (Retry)',
        questions: wrongQuestions.map(q => ({
            id: q.question.id,
            question: q.question.question,
            options: q.question.options,
            correct_answer: q.correct_answer,
            explanation: q.explanation
        }))
    };
    
    currentQuestionIndex = 0;
    userAnswers = {};
    quizStartTime = Date.now();
    startTimer();
    
    document.getElementById('quizResults').style.display = 'none';
    document.getElementById('quizInterface').style.display = 'block';
    document.getElementById('totalQuestions').textContent = currentQuiz.questions.length;
    
    loadQuestion();
    showToast(`Retrying ${wrongQuestions.length} wrong questions`, 'success');
}

// New quiz
function newQuiz() {
    currentQuiz = null;
    currentQuestionIndex = 0;
    userAnswers = {};
    
    document.getElementById('quizSetup').style.display = 'block';
    document.getElementById('quizInterface').style.display = 'none';
    document.getElementById('quizResults').style.display = 'none';
    
    clearInterval(timerInterval);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}