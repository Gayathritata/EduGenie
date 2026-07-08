/* File: app/static/js/ai_features.js */
/* Single Page App Sidebar Navigation, Q&A, Summaries, Explanations, Profiles, and Bookmarks */

document.addEventListener('DOMContentLoaded', () => {
    // Only execute on Dashboard workspace
    if (!document.querySelector('.dashboard-container')) return;

    initNavigation();
    loadDashboardHome();
    initMobileMenu();
});

/* Navigation Router */
function initNavigation() {
    const menuItems = document.querySelectorAll('.menu-item[data-section]');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Switch active classes
            menuItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Close mobile sidebar if open
            if (sidebar) sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
            
            const targetSection = item.dataset.section;
            switchSection(targetSection);
        });
    });
}

function initMobileMenu() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            const isOpen = sidebar && sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('active');
            // Update ARIA state for screen readers
            menuBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });
    }
    if (overlay) {
        overlay.addEventListener('click', () => {
            if (sidebar) sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
            const btn = document.querySelector('.mobile-menu-btn');
            if (btn) btn.setAttribute('aria-expanded', 'false');
        });
    }
}

function switchSection(sectionName) {
    const titleElement = document.querySelector('.navbar-title');
    const contentArea = document.getElementById('dynamic-workspace-content');
    
    // Set Header
    titleElement.textContent = capitalizeFirstLetter(sectionName.replace('-', ' '));
    
    // Clear and mount sections dynamically
    contentArea.innerHTML = getLoadingSpinnerHTML("Consulting EduGenie AI Engine...");

    switch (sectionName) {
        case 'dashboard-home':
            loadDashboardHome();
            break;
        case 'qa':
            mountQAForm(contentArea);
            break;
        case 'explain':
            mountExplainForm(contentArea);
            break;
        case 'summarize':
            mountSummarizeForm(contentArea);
            break;
        case 'roadmap':
            mountRoadmapView(contentArea);
            break;
        case 'quiz':
            mountQuizView(contentArea);
            break;
        case 'history':
            loadHistoryTimeline(contentArea);
            break;
        case 'saved':
            loadSavedResponses(contentArea);
            break;
        case 'profile':
            loadProfileView(contentArea);
            break;
        default:
            loadDashboardHome();
    }
}

/* -----------------------------------------------------
   Dashboard Home View Loader
   ----------------------------------------------------- */
async function loadDashboardHome() {
    const contentArea = document.getElementById('dynamic-workspace-content');
    const titleElement = document.querySelector('.navbar-title');
    if (titleElement) titleElement.textContent = 'Overview';
    
    try {
        const historyData = await APIClient.get('/history');
        const savedData = await APIClient.get('/save');
        
        const totalQueries = historyData.length;
        const totalBookmarks = savedData.length;
        const activeRoadmaps = historyData.filter(h => h.action === "generated_roadmap").length;
        const quizzesTaken = historyData.filter(h => h.action === "completed_quiz").length;

        contentArea.innerHTML = `
            <div class="animated">
                <div class="section-header">
                    <h2>Welcome back to your workspace!</h2>
                    <p>Track your academic achievements, configure personal roadmap targets, and review quizzes.</p>
                </div>
                
                <div class="dashboard-grid">
                    <div class="glass-panel stat-card">
                        <h4>Total AI Inquiries</h4>
                        <div style="display:flex; align-items:center; gap:12px; margin-top:8px;">
                            <div class="value">${totalQueries}</div>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" stroke-width="2" opacity="0.5" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        </div>
                    </div>
                    <div class="glass-panel stat-card">
                        <h4>Roadmaps Generated</h4>
                        <div style="display:flex; align-items:center; gap:12px; margin-top:8px;">
                            <div class="value">${activeRoadmaps}</div>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" stroke-width="2" opacity="0.5" aria-hidden="true"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                        </div>
                    </div>
                    <div class="glass-panel stat-card">
                        <h4>Quizzes Completed</h4>
                        <div style="display:flex; align-items:center; gap:12px; margin-top:8px;">
                            <div class="value">${quizzesTaken}</div>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-success)" stroke-width="2" opacity="0.5" aria-hidden="true"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                        </div>
                    </div>
                    <div class="glass-panel stat-card">
                        <h4>Bookmarked Responses</h4>
                        <div style="display:flex; align-items:center; gap:12px; margin-top:8px;">
                            <div class="value">${totalBookmarks}</div>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-warning)" stroke-width="2" opacity="0.5" aria-hidden="true"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
                        </div>
                    </div>
                </div>

                <div class="glass-panel input-panel">
                    <h3 style="margin-bottom:12px;">Quick Start</h3>
                    <p style="color:#94a3b8; margin-bottom:24px; line-height:1.6;">
                        Select a feature below or from the left sidebar to begin your learning session.
                    </p>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:12px;">
                        <button class="btn-secondary" style="padding:12px 16px; text-align:left; gap:10px; flex-direction:column; align-items:flex-start; height:auto;" onclick="document.querySelector('[data-section=\'qa\']').click()">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" stroke-width="2" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                            <span style="font-size:0.85rem;">Ask a Question</span>
                        </button>
                        <button class="btn-secondary" style="padding:12px 16px; text-align:left; gap:10px; flex-direction:column; align-items:flex-start; height:auto;" onclick="document.querySelector('[data-section=\'explain\']').click()">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" stroke-width="2" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                            <span style="font-size:0.85rem;">Explain a Concept</span>
                        </button>
                        <button class="btn-secondary" style="padding:12px 16px; text-align:left; gap:10px; flex-direction:column; align-items:flex-start; height:auto;" onclick="document.querySelector('[data-section=\'roadmap\']').click()">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" stroke-width="2" aria-hidden="true"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            <span style="font-size:0.85rem;">Generate Roadmap</span>
                        </button>
                        <button class="btn-secondary" style="padding:12px 16px; text-align:left; gap:10px; flex-direction:column; align-items:flex-start; height:auto;" onclick="document.querySelector('[data-section=\'quiz\']').click()">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-success)" stroke-width="2" aria-hidden="true"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                            <span style="font-size:0.85rem;">Take a Quiz</span>
                        </button>
                        <button class="btn-secondary" style="padding:12px 16px; text-align:left; gap:10px; flex-direction:column; align-items:flex-start; height:auto;" onclick="document.querySelector('[data-section=\'summarize\']').click()">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-warning)" stroke-width="2" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                            <span style="font-size:0.85rem;">Summarize Text</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        contentArea.innerHTML = `<div class="glass-panel input-panel animated"><p style="color:var(--accent-error);">Failed to load stats: ${err.message}</p></div>`;
    }
}

/* -----------------------------------------------------
   QA View Implementation
   ----------------------------------------------------- */
function mountQAForm(container) {
    container.innerHTML = `
        <div class="animated">
            <div class="glass-panel input-panel">
                <div class="form-group">
                    <label for="qa-question">Your Question</label>
                    <textarea id="qa-question" class="form-input" placeholder="e.g. How does backpropagation work in deep neural networks?"></textarea>
                </div>
                <div class="form-group">
                    <label for="qa-context">Reference Context (Optional)</label>
                    <textarea id="qa-context" class="form-input" style="min-height:80px;" placeholder="Paste textbook paragraphs or code snippets here to assist the model..."></textarea>
                </div>
                <button class="btn-primary" id="qa-submit-btn">Consult Co-Pilot</button>
            </div>
            <div class="glass-panel output-panel" id="qa-output" style="display:none;"></div>
        </div>
    `;

    document.getElementById('qa-submit-btn').addEventListener('click', async () => {
        const question = document.getElementById('qa-question').value.trim();
        const context = document.getElementById('qa-context').value.trim() || null;
        const outputDiv = document.getElementById('qa-output');
        const submitBtn = document.getElementById('qa-submit-btn');

        if (!question) return;

        setLoadingBtn(submitBtn, true);
        outputDiv.style.display = 'block';
        outputDiv.innerHTML = getLoadingSpinnerHTML("Thinking...");

        try {
            const data = await APIClient.post('/qa', { question, context });
            outputDiv.innerHTML = `
                <div class="section-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <h3>Co-Pilot Response</h3>
                    <button class="btn-secondary" style="padding: 8px 16px; font-size: 0.8rem;" id="save-qa-btn" data-id="${data.session_id}">Bookmark Response</button>
                </div>
                <div class="response-container">${formatMarkdown(data.answer)}</div>
            `;
            
            document.getElementById('save-qa-btn').addEventListener('click', () => {
                saveResponseBookmark(data.session_id, `QA: ${question.substring(0, 30)}...`, 'qa', data.answer);
            });
        } catch (err) {
            outputDiv.innerHTML = `<p style="color:var(--accent-error);">Error: ${err.message}</p>`;
        } finally {
            setLoadingBtn(submitBtn, false);
        }
    });
}

/* -----------------------------------------------------
   Concept Explanation View
   ----------------------------------------------------- */
function mountExplainForm(container) {
    container.innerHTML = `
        <div class="animated">
            <div class="glass-panel input-panel">
                <div class="form-group">
                    <label for="explain-concept">Concept to Explain</label>
                    <input type="text" id="explain-concept" class="form-input" placeholder="e.g. Quantum Entanglement, Closures in JS, Photosynthesis">
                </div>
                <div class="form-group">
                    <label for="explain-depth">Explanation Target Level</label>
                    <select id="explain-depth" class="form-input" style="background:#0d1222;">
                        <option value="beginner">Beginner (Uses simple analogies and visual concepts)</option>
                        <option value="intermediate">Intermediate (Standard definitions & code/formula examples)</option>
                        <option value="advanced">Advanced (Deep dive formulas, performance trade-offs, algorithms)</option>
                    </select>
                </div>
                <button class="btn-primary" id="explain-submit-btn">Explain Concept</button>
            </div>
            <div class="glass-panel output-panel" id="explain-output" style="display:none;"></div>
        </div>
    `;

    document.getElementById('explain-submit-btn').addEventListener('click', async () => {
        const concept = document.getElementById('explain-concept').value.trim();
        const depth = document.getElementById('explain-depth').value;
        const outputDiv = document.getElementById('explain-output');
        const submitBtn = document.getElementById('explain-submit-btn');

        if (!concept) return;

        setLoadingBtn(submitBtn, true);
        outputDiv.style.display = 'block';
        outputDiv.innerHTML = getLoadingSpinnerHTML("Analyzing and generating explanations...");

        try {
            const data = await APIClient.post('/explain', { concept, depth_level: depth });
            outputDiv.innerHTML = `
                <div class="section-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <h3>Explanation Core</h3>
                    <button class="btn-secondary" style="padding: 8px 16px; font-size: 0.8rem;" id="save-explain-btn" data-id="${data.session_id}">Bookmark Response</button>
                </div>
                <div class="response-container">${formatMarkdown(data.explanation)}</div>
            `;

            document.getElementById('save-explain-btn').addEventListener('click', () => {
                saveResponseBookmark(data.session_id, `Explain: ${concept}`, 'qa', data.explanation);
            });
        } catch (err) {
            outputDiv.innerHTML = `<p style="color:var(--accent-error);">Error: ${err.message}</p>`;
        } finally {
            setLoadingBtn(submitBtn, false);
        }
    });
}

/* -----------------------------------------------------
   Summarization View
   ----------------------------------------------------- */
function mountSummarizeForm(container) {
    container.innerHTML = `
        <div class="animated">
            <div class="glass-panel input-panel">
                <div class="form-group">
                    <label for="summ-text">Text Content to Summarize</label>
                    <textarea id="summ-text" class="form-input" style="min-height:160px;" placeholder="Paste long articles, textbook definitions, or documentation sheets here..."></textarea>
                </div>
                <div class="form-group">
                    <label for="summ-length">Target Summary Length</label>
                    <select id="summ-length" class="form-input" style="background:#0d1222;">
                        <option value="short">Short (1-3 sentences capturing key takeaway)</option>
                        <option value="medium" selected>Medium (Concise list of 3-5 key bullets)</option>
                        <option value="long">Long (Detailed analytical summary paragraphs)</option>
                    </select>
                </div>
                <button class="btn-primary" id="summ-submit-btn">Summarize Document</button>
            </div>
            <div class="glass-panel output-panel" id="summ-output" style="display:none;"></div>
        </div>
    `;

    document.getElementById('summ-submit-btn').addEventListener('click', async () => {
        const text = document.getElementById('summ-text').value.trim();
        const length = document.getElementById('summ-length').value;
        const outputDiv = document.getElementById('summ-output');
        const submitBtn = document.getElementById('summ-submit-btn');

        if (!text || text.length < 10) return;

        setLoadingBtn(submitBtn, true);
        outputDiv.style.display = 'block';
        outputDiv.innerHTML = getLoadingSpinnerHTML("Running NLP summarizer...");

        try {
            const data = await APIClient.post('/summarize', { text, target_length: length });
            outputDiv.innerHTML = `
                <div class="section-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <h3>Document Summary</h3>
                    <button class="btn-secondary" style="padding: 8px 16px; font-size: 0.8rem;" id="save-summ-btn" data-id="${data.session_id}">Bookmark Response</button>
                </div>
                <div class="response-container">${formatMarkdown(data.summary)}</div>
            `;

            document.getElementById('save-summ-btn').addEventListener('click', () => {
                saveResponseBookmark(data.session_id, `Summary: ${text.substring(0, 25)}...`, 'summary', data.summary);
            });
        } catch (err) {
            outputDiv.innerHTML = `<p style="color:var(--accent-error);">Error: ${err.message}</p>`;
        } finally {
            setLoadingBtn(submitBtn, false);
        }
    });
}

/* -----------------------------------------------------
   Saved Bookmarks Loader
   ----------------------------------------------------- */
async function loadSavedResponses(container) {
    try {
        const savedData = await APIClient.get('/save');
        
        if (savedData.length === 0) {
            container.innerHTML = `
                <div class="empty-state-card animated">
                    <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                    </svg>
                    <h4>No Bookmarks Saved</h4>
                    <p>When you consult EduGenie Q&A or generate study roadmaps, you can bookmark answers to compile a personal knowledge archive.</p>
                    <button class="btn-primary" onclick="document.querySelector('[data-section=\\'qa\\']').click()">Ask a Question</button>
                </div>
            `;
            return;
        }

        let listHTML = `<div class="history-list animated">`;
        savedData.forEach(item => {
            const date = new Date(item.created_at).toLocaleDateString();
            listHTML += `
                <div class="glass-panel history-item" id="saved-item-${item.id}">
                    <div class="details">
                        <h5>${escapeHTML(item.title)}</h5>
                        <p>Category: <strong style="color:var(--accent-primary); text-transform:uppercase;">${item.category}</strong> | Date: ${date}</p>
                        <div class="response-container" style="margin-top:12px; display:none;" id="saved-content-${item.id}">
                            ${formatMarkdown(item.content)}
                        </div>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button class="btn-secondary" style="padding:8px 16px; font-size:0.8rem;" onclick="toggleSavedItem(${item.id})">Expand/Collapse</button>
                        <button class="btn-secondary" style="padding:8px 16px; font-size:0.8rem; border-color:var(--accent-error); color:var(--accent-error);" onclick="deleteSavedItem(${item.id})">Remove</button>
                    </div>
                </div>
            `;
        });
        listHTML += `</div>`;
        container.innerHTML = listHTML;
    } catch (err) {
        container.innerHTML = `<p style="color:var(--accent-error);">Failed to load bookmarks: ${err.message}</p>`;
    }
}

window.toggleSavedItem = function(id) {
    const el = document.getElementById(`saved-content-${id}`);
    if (el.style.display === 'none') {
        el.style.display = 'block';
    } else {
        el.style.display = 'none';
    }
};

window.deleteSavedItem = async function(id) {
    if (!confirm('Are you sure you want to remove this bookmark?')) return;
    try {
        await APIClient.delete(`/save/${id}`);
        const el = document.getElementById(`saved-item-${id}`);
        if (el) el.remove();
        showNotification('Bookmark successfully removed!', 'success');
    } catch (err) {
        showNotification('Failed to remove bookmark: ' + err.message, 'error');
    }
};

/* -----------------------------------------------------
   User History Logs Timeline
   ----------------------------------------------------- */
async function loadHistoryTimeline(container) {
    try {
        const historyData = await APIClient.get('/history');
        
        if (historyData.length === 0) {
            container.innerHTML = `
                <div class="empty-state-card animated">
                    <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <h4>Timeline Log is Empty</h4>
                    <p>Interact with the Q&A co-pilot, explain complex terms, or generate customized milestone roadmaps to populate your activity logs.</p>
                    <button class="btn-primary" onclick="document.querySelector('[data-section=\\'roadmap\\']').click()">Generate Roadmap</button>
                </div>
            `;
            return;
        }

        let listHTML = `<div class="history-list animated">`;
        historyData.forEach(log => {
            const date = new Date(log.created_at).toLocaleString();
            const actionLabel = log.action
                ? log.action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                : 'Activity';
            listHTML += `
                <div class="glass-panel history-item">
                    <div class="details">
                        <h5>${escapeHTML(log.description)}</h5>
                        <p>Action: <strong style="color:var(--accent-primary); font-size:0.8rem; text-transform:uppercase; letter-spacing:0.5px; padding:2px 6px; background:rgba(0,242,254,0.06); border-radius:4px;">${escapeHTML(actionLabel)}</strong> | Target: ${escapeHTML(log.entity_type || 'N/A')}</p>
                    </div>
                    <div class="time">${date}</div>
                </div>
            `;
        });
        listHTML += `</div>`;
        container.innerHTML = listHTML;
    } catch (err) {
        container.innerHTML = `<p style="color:var(--accent-error);">Failed to load history logs: ${err.message}</p>`;
    }
}

/* -----------------------------------------------------
   User Profile View
   ----------------------------------------------------- */
async function loadProfileView(container) {
    try {
        const user = await APIClient.get('/profile');
        const date = new Date(user.created_at).toLocaleDateString();
        
        container.innerHTML = `
            <div class="glass-panel input-panel animated" style="max-width:600px; margin: 0 auto;">
                <div style="display:flex; flex-direction:column; align-items:center; margin-bottom:30px; gap:16px;">
                    <div class="avatar" style="width:70px; height:70px; font-size:1.8rem; border-radius:50%;">${user.username[0].toUpperCase()}</div>
                    <h3 style="font-size:1.5rem; font-weight:700;">${escapeHTML(user.username)}</h3>
                    <p style="color:#64748b; font-size:0.9rem;">Verified Student Profile</p>
                </div>
                
                <div style="display:flex; flex-direction:column; gap:16px;">
                    <div style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid var(--border-color);">
                        <span style="color:#94a3b8;">Email Address</span>
                        <span style="font-weight:600;">${escapeHTML(user.email)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid var(--border-color);">
                        <span style="color:#94a3b8;">Student ID</span>
                        <span style="font-weight:600; font-family:monospace;">#EG-${user.id}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid var(--border-color);">
                        <span style="color:#94a3b8;">Registered Date</span>
                        <span style="font-weight:600;">${date}</span>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<p style="color:var(--accent-error);">Failed to load profile details: ${err.message}</p>`;
    }
}

/* -----------------------------------------------------
   Core Helpers
   ----------------------------------------------------- */
async function saveResponseBookmark(sessionId, title, category, content) {
    try {
        await APIClient.post('/save', {
            source_response_id: sessionId,
            title,
            category,
            content
        });
        showNotification('Response successfully bookmarked!', 'success');
    } catch (err) {
        showNotification('Failed to bookmark: ' + err.message, 'error');
    }
}

function getLoadingSpinnerHTML(text = "Processing...") {
    return `
        <div class="spinner-container">
            <div class="spinner"></div>
            <div class="spinner-text">${text}</div>
        </div>
    `;
}

function setLoadingBtn(btn, isLoading) {
    if (isLoading) {
        btn.disabled = true;
        btn.dataset.original = btn.innerHTML;
        btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;margin:0;"></span> Processing...';
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.original || 'Submit';
    }
}

function capitalizeFirstLetter(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHTML(str) {
    if (!str) return '';
    return String(str).replace(/[&<>'"` ]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;', '`': '&#96;', ' ': ' ' }[tag] || tag)
    );
}

/* Simple Markdown formatter for educational formatting */
function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHTML(text);
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Code blocks (pre/code) with premium copy button
    html = html.replace(/```(?:\w+)?\n([\s\S]*?)```/g, (match, code) => {
        return `
            <div class="code-block-wrapper">
                <button class="copy-code-btn" onclick="copyCodeToClipboard(this)">Copy</button>
                <pre><code>${code}</code></pre>
            </div>
        `;
    });
    
    // Inline code
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Headings
    html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
    
    // Lists — collect consecutive li items and wrap in ul
    html = html.replace(/^[*\-] (.*?)$/gm, '<li>$1</li>');
    // Wrap consecutive <li> blocks in <ul>
    html = html.replace(/(<li>.*?<\/li>\n?)+/gs, match => `<ul>${match}</ul>`);

    // Numbered lists
    html = html.replace(/^\d+\. (.*?)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*?<\/li>\n?)+/gs, match => {
        // Only wrap if not already inside <ul>
        if (!match.includes('<ul>')) return `<ul>${match}</ul>`;
        return match;
    });
    
    // Paragraphs — blank lines become paragraph breaks
    html = html.replace(/\n\n+/g, '</p><p>');

    return html;
}

/* Global copy-to-clipboard handler */
window.copyCodeToClipboard = function(btn) {
    const pre = btn.nextElementSibling;
    const code = pre.querySelector('code');
    const textToCopy = code.innerText || code.textContent;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        btn.textContent = 'Copied!';
        btn.style.background = 'var(--accent-success)';
        btn.style.color = '#050510';
        setTimeout(() => {
            btn.textContent = 'Copy';
            btn.style.background = '';
            btn.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Could not copy code: ', err);
        showNotification('Failed to copy to clipboard', 'error');
    });
};
