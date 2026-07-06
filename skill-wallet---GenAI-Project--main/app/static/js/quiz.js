/* File: app/static/js/quiz.js */
/* Quiz Generators, MCQ choice panels, Timer Submissions, and Graded evaluations */

let activeQuizTimer = null;
let quizSecondsElapsed = 0;
let lastQuizParams = null; // Store last params to support 'Retry Quiz' feature

function mountQuizView(container) {
    // Clear any active timer instances
    if (activeQuizTimer) clearInterval(activeQuizTimer);
    
    container.innerHTML = `
        <div class="animated">
            <div class="glass-panel input-panel">
                <div class="section-header">
                    <h2>Advanced Quiz Arena</h2>
                    <p>Test your educational retention with dynamic multiple-choice questions powered by Google Gemini.</p>
                </div>
                
                <div class="form-group">
                    <label for="quiz-topic">Quiz Topic</label>
                    <input type="text" id="quiz-topic" class="form-input" placeholder="e.g. Python List Comprehensions, CSS Grids, DNA Transcription">
                </div>
                <div class="form-group">
                    <label for="quiz-diff">Difficulty Level</label>
                    <select id="quiz-diff" class="form-input" style="background:#0d1222;">
                        <option value="Beginner">Beginner (Fundamentals & simple terms)</option>
                        <option value="Intermediate" selected>Intermediate (Standard rules & implementations)</option>
                        <option value="Advanced">Advanced (Deep math, edge cases, optimizations)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="quiz-count">Number of Questions</label>
                    <select id="quiz-count" class="form-input" style="background:#0d1222;">
                        <option value="3" selected>3 Questions (Recommended)</option>
                        <option value="5">5 Questions</option>
                        <option value="10">10 Questions</option>
                    </select>
                </div>
                <button class="btn-primary" id="quiz-submit-btn">Generate Quiz</button>
            </div>
            <div class="glass-panel output-panel" id="quiz-output" style="display:none;"></div>
        </div>
    `;

    document.getElementById('quiz-submit-btn').addEventListener('click', () => {
        const topic = document.getElementById('quiz-topic').value.trim();
        const difficulty = document.getElementById('quiz-diff').value;
        const count = document.getElementById('quiz-count').value;
        
        if (!topic) {
            showNotification('Please enter a study topic.', 'error');
            return;
        }

        generateQuizAction(topic, parseInt(count), difficulty);
    });
}

async function generateQuizAction(topic, count, difficulty) {
    const outputDiv = document.getElementById('quiz-output');
    const submitBtn = document.getElementById('quiz-submit-btn');

    // Save params for retry feature
    lastQuizParams = { topic, count, difficulty };

    setLoadingBtn(submitBtn, true);
    outputDiv.style.display = 'block';
    outputDiv.innerHTML = getLoadingSpinnerHTML(`Formulating ${count} ${difficulty} level questions on '${topic}'...`);

    try {
        const data = await APIClient.post('/quiz', { topic, num_questions: count, difficulty });
        renderQuizQuestions(outputDiv, data);
        showNotification('Quiz successfully generated!', 'success');
    } catch (err) {
        outputDiv.innerHTML = `<p style="color:var(--accent-error);">Error: {err.message}</p>`;
        showNotification(err.message, 'error');
    } finally {
        setLoadingBtn(submitBtn, false);
    }
}

function renderQuizQuestions(container, quiz) {
    const questions = quiz.questions || [];
    
    let html = `
        <div class="section-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; border-bottom:1px solid var(--border-color); padding-bottom:16px;">
            <div>
                <h3>Topic: ${escapeHTML(quiz.topic)}</h3>
                <p style="color:#64748b; font-size:0.85rem; margin-top:4px;">
                    Difficulty: <strong style="color:var(--accent-primary);">${quiz.difficulty || 'Intermediate'}</strong> | 
                    Total: <strong>${questions.length} questions</strong>
                </p>
            </div>
            <div style="text-align:right;">
                <p style="color:#64748b; font-size:0.85rem;" id="quiz-timer-display">Time elapsed: 00:00</p>
            </div>
        </div>
        <form id="quiz-questions-form" data-quiz-id="${quiz.quiz_id}">
    `;

    questions.forEach((q, qIdx) => {
        const choices = q.choices || [];
        const alphabet = ['A', 'B', 'C', 'D'];
        
        html += `
            <div class="quiz-question-card" id="question-card-${q.id}">
                <h4 style="font-weight:600; margin-bottom:14px;">Q${qIdx + 1}. ${escapeHTML(q.question)}</h4>
                <div class="quiz-choices">
        `;
        
        choices.forEach((choice, cIdx) => {
            const letter = alphabet[cIdx] || 'A';
            html += `
                <label class="choice-label" id="choice-label-${q.id}-${letter}">
                    <input type="radio" name="question_${q.id}" value="${letter}" required>
                    <span><strong>${letter}.</strong> ${escapeHTML(choice)}</span>
                </label>
            `;
        });

        html += `
                </div>
            </div>
        `;
    });

    html += `
            <button type="submit" class="btn-primary" style="margin-top:20px; width:100%; padding:14px;">Submit Answers</button>
        </form>
    `;

    container.innerHTML = html;
    
    // Start Timer
    quizSecondsElapsed = 0;
    const timerDisplay = document.getElementById('quiz-timer-display');
    if (activeQuizTimer) clearInterval(activeQuizTimer);
    
    activeQuizTimer = setInterval(() => {
        quizSecondsElapsed++;
        const mins = String(Math.floor(quizSecondsElapsed / 60)).padStart(2, '0');
        const secs = String(quizSecondsElapsed % 60).padStart(2, '0');
        timerDisplay.textContent = `Time elapsed: ${mins}:${secs}`;
    }, 1000);

    // Form submission
    const form = document.getElementById('quiz-questions-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearInterval(activeQuizTimer);
        
        const quizId = form.dataset.quizId;
        const answers = {};
        
        questions.forEach(q => {
            const checked = form.querySelector(`input[name="question_${q.id}"]:checked`);
            answers[String(q.id)] = checked ? checked.value : '';
        });

        const submitBtn = form.querySelector('button[type="submit"]');
        setLoadingBtn(submitBtn, true);

        try {
            const data = await APIClient.post('/quiz/submit', { quiz_id: parseInt(quizId), answers });
            renderGradedQuizResults(container, data);
            showNotification('Quiz submitted successfully! Scoring calculated.', 'success');
        } catch (err) {
            showNotification('Failed to grade quiz: ' + err.message, 'error');
        } finally {
            setLoadingBtn(submitBtn, false);
        }
    });
}

function renderGradedQuizResults(container, graded) {
    const results = graded.results || [];
    const score = graded.score;
    const total = graded.total;
    const percentage = Math.round((score / total) * 100);
    
    let html = `
        <div class="section-header" style="text-align:center; margin-bottom:30px; border-bottom:1px solid var(--border-color); padding-bottom:24px;">
            <p style="color:#64748b; font-size:0.9rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">Your Quiz Result</p>
            <h3 style="font-size:2.5rem; font-weight:800; color:var(--accent-primary); margin:0;">${score} / ${total}</h3>
            <p style="font-size:1.15rem; color:#fff; font-weight:600; margin-top:8px;">Accuracy: ${percentage}%</p>
            
            <div style="display:flex; justify-content:center; gap:16px; margin-top:20px;">
                <button class="btn-primary" style="padding: 10px 24px;" id="retry-quiz-btn">Retry Quiz</button>
                <button class="btn-secondary" style="padding: 10px 24px;" onclick="document.querySelector('[data-section=\\'quiz\\']').click()">New Topic</button>
            </div>
        </div>
    `;

    results.forEach((res, idx) => {
        const isCorrect = res.is_correct;
        const correctKey = res.correct_key;
        const userKey = res.user_key;
        
        html += `
            <div class="quiz-question-card" style="border-color:${isCorrect ? 'var(--accent-success)' : 'var(--accent-error)'}; background:rgba(255,255,255,0.015);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                    <h4 style="margin:0; font-weight:600;">Q${idx + 1}. ${escapeHTML(res.question)}</h4>
                    <span style="font-weight:700; color:${isCorrect ? 'var(--accent-success)' : 'var(--accent-error)'}; font-size:0.8rem; text-transform:uppercase; padding:4px 8px; border-radius:4px; background:rgba(255,255,255,0.03);">
                        ${isCorrect ? 'Correct' : 'Incorrect'}
                    </span>
                </div>
                
                <div style="display:flex; flex-direction:column; gap:10px; margin-bottom:16px;">
                    <div class="choice-label ${correctKey === userKey ? 'grade-correct' : 'grade-selected-incorrect'}" style="cursor:default;">
                        <span><strong>Selected Choice:</strong> ${userKey || 'No option selected'}</span>
                    </div>
                    ${correctKey !== userKey ? `
                        <div class="choice-label grade-correct" style="cursor:default;">
                            <span><strong>Correct Choice:</strong> ${correctKey}</span>
                        </div>
                    ` : ''}
                </div>
                
                <div class="quiz-explanation">
                    <strong>Gemini Explanation:</strong> ${escapeHTML(res.explanation)}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;

    // Retry Quiz Action Handler
    document.getElementById('retry-quiz-btn').addEventListener('click', () => {
        if (lastQuizParams) {
            generateQuizAction(lastQuizParams.topic, lastQuizParams.count, lastQuizParams.difficulty);
        }
    });
}
