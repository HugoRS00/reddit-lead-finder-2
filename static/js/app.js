document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        keywords: [],
        platforms: ['reddit'],
        results: []
    };

    // Elements
    const keywordInput = document.getElementById('keywordInput');
    const addKeywordBtn = document.getElementById('addKeywordBtn');
    const keywordsList = document.getElementById('keywordsList');
    const scanBtn = document.getElementById('scanBtn');
    const resultsContainer = document.getElementById('resultsContainer');
    const replyModal = document.getElementById('replyModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const modalBody = document.getElementById('modalBody');

    // Initialize
    loadDefaultKeywords();

    // Event Listeners
    addKeywordBtn.addEventListener('click', addKeyword);
    keywordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addKeyword();
    });

    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const platform = e.target.dataset.platform;
            e.target.classList.toggle('active');

            if (state.platforms.includes(platform)) {
                state.platforms = state.platforms.filter(p => p !== platform);
            } else {
                state.platforms.push(platform);
            }
        });
    });

    scanBtn.addEventListener('click', runScan);
    closeModalBtn.addEventListener('click', () => {
        replyModal.classList.remove('active');
    });

    // Functions
    async function loadDefaultKeywords() {
        try {
            const res = await fetch('/api/default-keywords');
            const data = await res.json();
            data.keywords.forEach(kw => addKeywordToState(kw));
        } catch (e) {
            console.error('Failed to load defaults', e);
        }
    }

    function addKeyword() {
        const val = keywordInput.value.trim();
        if (val && !state.keywords.includes(val)) {
            addKeywordToState(val);
            keywordInput.value = '';
        }
    }

    function addKeywordToState(kw) {
        state.keywords.push(kw);
        renderKeywords();
    }

    function removeKeyword(kw) {
        state.keywords = state.keywords.filter(k => k !== kw);
        renderKeywords();
    }

    function renderKeywords() {
        keywordsList.innerHTML = state.keywords.map(kw => `
            <span class="keyword-tag" onclick="removeKeyword('${kw}')">
                ${kw} &times;
            </span>
        `).join('');
    }

    window.removeKeyword = removeKeyword; // Make global for onclick

    async function runScan() {
        if (state.keywords.length === 0) {
            alert('Please add at least one keyword');
            return;
        }

        setLoading(true);
        resultsContainer.innerHTML = '';

        const payload = {
            keywords: state.keywords,
            platforms: state.platforms,
            date_range: document.getElementById('dateRange').value,
            min_followers: document.getElementById('minFollowers').value,
            min_engagement: document.getElementById('minEngagement').value
        };

        try {
            const res = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (data.success) {
                state.results = data.results;
                renderResults(data.results);
                updateStats(data.count);
            } else {
                alert('Scan failed: ' + (data.error || 'Unknown error'));
            }
        } catch (e) {
            console.error(e);
            alert('Scan error');
        } finally {
            setLoading(false);
        }
    }

    function renderResults(results) {
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div style="text-align:center; padding: 2rem; color: var(--text-muted);">No leads found. Try different keywords.</div>';
            return;
        }

        resultsContainer.innerHTML = results.map((item, index) => `
            <div class="lead-card">
                <div class="card-header">
                    <span class="platform-badge platform-${item.source}">${item.source}</span>
                    <span class="score-badge">Score: ${item.score}</span>
                </div>
                <div class="card-content">
                    <h3><a href="${item.url}" target="_blank" style="color: inherit; text-decoration: none;">${item.title}</a></h3>
                    <p>${item.body}</p>
                </div>
                <div class="card-meta">
                    <span>${item.author}</span>
                    <span>${new Date(item.created_utc).toLocaleDateString()}</span>
                    <span>${item.intent_label || 'General'}</span>
                </div>
                <div class="card-actions">
                    <button class="action-btn btn-primary" onclick="generateReply(${index})">
                        ⚡ Generate Reply
                    </button>
                    <a href="${item.url}" target="_blank" class="action-btn btn-secondary">
                        🔗 View Post
                    </a>
                </div>
            </div>
        `).join('');

        // Expose function globally
        window.generateReply = (index) => handleGenerateReply(results[index]);
    }

    async function handleGenerateReply(item) {
        replyModal.classList.add('active');
        modalBody.innerHTML = '<div style="text-align:center; padding: 2rem;">Generating AI replies... <div class="loader" style="display:inline-block; border-color: var(--primary); border-top-color: transparent;"></div></div>';

        try {
            const res = await fetch('/api/generate-reply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    context: item.context || item.body,
                    intent_label: item.intent_label,
                    reply_mode: document.getElementById('replyMode').value,
                    reply_length: document.getElementById('replyLength').value,
                    voice_profile: {
                        name: document.getElementById('voiceName').value,
                        instructions: document.getElementById('voiceInstructions').value
                    }
                })
            });

            const data = await res.json();

            if (data.success) {
                renderVariants(data.variants);
            } else {
                modalBody.innerHTML = `<div style="color: var(--danger); text-align: center;">Error: ${data.error}</div>`;
            }
        } catch (e) {
            modalBody.innerHTML = `<div style="color: var(--danger); text-align: center;">Failed to generate reply</div>`;
        }
    }

    function renderVariants(variants) {
        modalBody.innerHTML = `
            <div class="reply-variants">
                ${variants.map(v => `
                    <div class="variant-card">
                        <div class="variant-header">
                            <span>Variant ${v.letter}</span>
                            <button class="copy-btn" onclick="navigator.clipboard.writeText(this.dataset.text)">
                                📋 Copy
                            </button>
                        </div>
                        <div style="white-space: pre-wrap; font-size: 0.95rem;">${v.reply}</div>
                    </div>
                `).join('')}
            </div>
        `;

        // Re-attach copy listeners since we used innerHTML
        document.querySelectorAll('.copy-btn').forEach((btn, i) => {
            btn.dataset.text = variants[i].reply;
            btn.addEventListener('click', function () {
                navigator.clipboard.writeText(this.dataset.text);
                const original = this.innerHTML;
                this.innerHTML = '✅ Copied!';
                setTimeout(() => this.innerHTML = original, 2000);
            });
        });
    }

    function updateStats(count) {
        document.getElementById('totalLeads').textContent = count;
    }

    function setLoading(isLoading) {
        if (isLoading) {
            scanBtn.classList.add('loading');
            scanBtn.disabled = true;
        } else {
            scanBtn.classList.remove('loading');
            scanBtn.disabled = false;
        }
    }
});
