/* File: app/static/js/roadmap.js */
/* Roadmap Form Handler and Interactive Recommendation Layout Renderer */

function mountRoadmapView(container) {
    container.innerHTML = `
        <div class="animated">
            <div class="glass-panel input-panel">
                <div class="section-header">
                    <h2>AI Learning Recommendation</h2>
                    <p>Formulate a comprehensive personalized curriculum, progressive milestones, projects, resources, and weekly plan.</p>
                </div>
                
                <div class="form-group">
                    <label for="roadmap-topic">Study Topic</label>
                    <input type="text" id="roadmap-topic" class="form-input" placeholder="e.g. Machine Learning, Organic Chemistry, Kubernetes">
                </div>
                <div class="form-group">
                    <label for="roadmap-diff">Starting Skill Level</label>
                    <select id="roadmap-diff" class="form-input" style="background:#0d1222;">
                        <option value="Beginner">Beginner (No prior experience)</option>
                        <option value="Intermediate" selected>Intermediate (Basic understanding and terminology)</option>
                        <option value="Advanced">Advanced (Operational competency seeking mastery)</option>
                    </select>
                </div>
                <button class="btn-primary" id="roadmap-submit-btn">Generate Recommendation</button>
            </div>
            <div class="glass-panel output-panel" id="roadmap-output" style="display:none;"></div>
        </div>
    `;

    document.getElementById('roadmap-submit-btn').addEventListener('click', async () => {
        const topic = document.getElementById('roadmap-topic').value.trim();
        const difficulty = document.getElementById('roadmap-diff').value;
        const outputDiv = document.getElementById('roadmap-output');
        const submitBtn = document.getElementById('roadmap-submit-btn');

        if (!topic) {
            showNotification('Please enter a study topic.', 'error');
            return;
        }

        setLoadingBtn(submitBtn, true);
        outputDiv.style.display = 'block';
        outputDiv.innerHTML = getLoadingSpinnerHTML("Consulting Gemini AI to build learning path and recommendations...");

        try {
            const data = await APIClient.post('/learn', { topic, difficulty });
            renderRoadmapData(outputDiv, data);
            showNotification('Learning Recommendation successfully generated!', 'success');
        } catch (err) {
            outputDiv.innerHTML = `<p style="color:var(--accent-error);">Error: ${err.message}</p>`;
            showNotification(err.message, 'error');
        } finally {
            setLoadingBtn(submitBtn, false);
        }
    });
}

function renderRoadmapData(container, data) {
    const rData = data.roadmap_data;
    const progression = rData.progression || {};
    const resources = rData.resources || {};
    const projects = rData.suggested_projects || [];
    const plan = rData.weekly_study_plan || [];

    let html = `
        <div class="animated">
            <!-- 1. Header with metadata -->
            <div class="section-header" style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px; border-bottom:1px solid var(--border-color); padding-bottom:20px;">
                <div>
                    <h3 style="font-size:1.8rem; font-weight:800; color:#fff;">Learning Recommendation: ${escapeHTML(data.topic)}</h3>
                    <p style="color:#64748b; font-size:0.9rem; margin-top:4px;">
                        Starting Level: <strong style="color:var(--accent-primary);">${data.difficulty}</strong> | 
                        Estimated Time: <strong style="color:var(--accent-secondary);">${escapeHTML(rData.estimated_time || '8 Weeks')}</strong>
                    </p>
                </div>
                <button class="btn-secondary" style="padding: 10px 20px; font-size: 0.85rem;" id="save-roadmap-btn" data-id="${data.roadmap_id}">Bookmark Path</button>
            </div>

            <!-- Overview -->
            <div style="margin-bottom:30px; line-height:1.6; color:#cbd5e1;">
                <p>${escapeHTML(rData.overview || 'Overview not available.')}</p>
            </div>

            <!-- 2. Progression Tiers Grid -->
            <h4 style="font-size:1.1rem; font-weight:700; margin-bottom:16px; color:#fff;">Progression Milestones</h4>
            <div class="dashboard-grid" style="margin-bottom:35px;">
                <div class="glass-panel stat-card" style="border-top: 4px solid var(--accent-secondary);">
                    <h4 style="color:var(--accent-secondary); font-size:0.8rem;">1. Beginner Core</h4>
                    <p style="font-size:0.9rem; color:#94a3b8; line-height:1.5; margin-top:8px;">${escapeHTML(progression.beginner || 'N/A')}</p>
                </div>
                <div class="glass-panel stat-card" style="border-top: 4px solid var(--accent-primary);">
                    <h4 style="color:var(--accent-primary); font-size:0.8rem;">2. Intermediate Core</h4>
                    <p style="font-size:0.9rem; color:#94a3b8; line-height:1.5; margin-top:8px;">${escapeHTML(progression.intermediate || 'N/A')}</p>
                </div>
                <div class="glass-panel stat-card" style="border-top: 4px solid var(--accent-purple);">
                    <h4 style="color:var(--accent-purple); font-size:0.8rem;">3. Advanced Core</h4>
                    <p style="font-size:0.9rem; color:#94a3b8; line-height:1.5; margin-top:8px;">${escapeHTML(progression.advanced || 'N/A')}</p>
                </div>
            </div>

            <!-- 3. Curated Resources (Tabs or Grid) -->
            <h4 style="font-size:1.1rem; font-weight:700; margin-bottom:16px; color:#fff;">Recommended Resources</h4>
            <div class="dashboard-grid" style="margin-bottom:35px;">
                <div class="glass-panel" style="padding:20px;">
                    <h5 style="color:var(--accent-primary); margin-bottom:12px; font-size:0.9rem; text-transform:uppercase;">Books</h5>
                    <ul style="list-style:none; padding:0; display:flex; flex-direction:column; gap:8px;">
                        ${(resources.books || []).map(b => `<li style="font-size:0.9rem; color:#94a3b8;">📖 ${escapeHTML(b)}</li>`).join('') || '<li style="color:#64748b; font-size:0.9rem;">None suggested.</li>'}
                    </ul>
                </div>
                <div class="glass-panel" style="padding:20px;">
                    <h5 style="color:var(--accent-primary); margin-bottom:12px; font-size:0.9rem; text-transform:uppercase;">YouTube Channels</h5>
                    <ul style="list-style:none; padding:0; display:flex; flex-direction:column; gap:8px;">
                        ${(resources.youtube || []).map(y => `<li style="font-size:0.9rem; color:#94a3b8;">📺 ${escapeHTML(y)}</li>`).join('') || '<li style="color:#64748b; font-size:0.9rem;">None suggested.</li>'}
                    </ul>
                </div>
                <div class="glass-panel" style="padding:20px;">
                    <h5 style="color:var(--accent-primary); margin-bottom:12px; font-size:0.9rem; text-transform:uppercase;">Online Courses</h5>
                    <ul style="list-style:none; padding:0; display:flex; flex-direction:column; gap:8px;">
                        ${(resources.courses || []).map(c => `<li style="font-size:0.9rem; color:#94a3b8;">🎓 ${escapeHTML(c)}</li>`).join('') || '<li style="color:#64748b; font-size:0.9rem;">None suggested.</li>'}
                    </ul>
                </div>
                <div class="glass-panel" style="padding:20px;">
                    <h5 style="color:var(--accent-primary); margin-bottom:12px; font-size:0.9rem; text-transform:uppercase;">Certifications</h5>
                    <ul style="list-style:none; padding:0; display:flex; flex-direction:column; gap:8px;">
                        ${(resources.certifications || []).map(cert => `<li style="font-size:0.9rem; color:#94a3b8;">🏅 ${escapeHTML(cert)}</li>`).join('') || '<li style="color:#64748b; font-size:0.9rem;">None suggested.</li>'}
                    </ul>
                </div>
            </div>

            <!-- 4. Projects Showcase -->
            <h4 style="font-size:1.1rem; font-weight:700; margin-bottom:16px; color:#fff;">Suggested Practical Projects</h4>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:35px;">
                ${projects.map(proj => `
                    <div class="glass-panel" style="padding:20px;">
                        <h5 style="font-weight:600; font-size:1rem; margin-bottom:8px; color:#fff;">${escapeHTML(proj.title)}</h5>
                        <p style="font-size:0.9rem; color:#94a3b8; line-height:1.5;">${escapeHTML(proj.description)}</p>
                    </div>
                `).join('')}
            </div>

            <!-- 5. Weekly Study Plan Timeline -->
            <h4 style="font-size:1.1rem; font-weight:700; margin-bottom:16px; color:#fff;">Weekly Study Plan</h4>
            <div class="roadmap-timeline">
                ${plan.map((w, idx) => `
                    <div class="roadmap-step">
                        <div class="step-num">Week ${w.week || idx + 1}</div>
                        <div class="step-title">${escapeHTML(w.focus)}</div>
                        
                        <div style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:12px; margin-top:12px;">
                            <div class="step-topics">
                                ${(w.topics || []).map(t => `<span class="topic-tag">${escapeHTML(t)}</span>`).join('')}
                            </div>
                            <button class="btn-primary" style="padding:8px 16px; font-size:0.8rem;" onclick="triggerRoadmapStepQuiz('${escapeHTML(w.checkpoint_quiz_topic || w.focus)}')">
                                Take Week Quiz
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Save/Bookmark path listener
    document.getElementById('save-roadmap-btn').addEventListener('click', () => {
        saveResponseBookmark(data.roadmap_id, `Roadmap: ${data.topic}`, 'roadmap', JSON.stringify(data.roadmap_data));
    });
}

window.triggerRoadmapStepQuiz = function(quizTopic) {
    const quizMenu = document.querySelector('[data-section="quiz"]');
    if (quizMenu) {
        quizMenu.click();
        
        setTimeout(() => {
            const topicInput = document.getElementById('quiz-topic');
            if (topicInput) {
                topicInput.value = quizTopic;
                document.getElementById('quiz-submit-btn').click();
            }
        }, 100);
    }
};
