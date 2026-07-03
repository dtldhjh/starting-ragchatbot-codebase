// API base URL - use relative path to work from any host
const API_URL = '/api';

// Sessions state: Map<localId, {localId, serverId, title, messages}>
const sessions = new Map();
let activeSessionId = null;
let sessionCounter = 0;

// DOM elements
let chatMessages, chatInput, sendButton, totalCourses, courseTitles, sessionsList;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    sessionsList = document.getElementById('sessionsList');

    setupEventListeners();
    initTheme();
    createNewSession();
    loadCourseStats();
});

// Event Listeners
function setupEventListeners() {
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    const themeToggle = document.getElementById('themeToggle');
    themeToggle.addEventListener('click', toggleTheme);

    const newSessionBtn = document.getElementById('newSessionBtn');
    newSessionBtn.addEventListener('click', createNewSession);

    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}

// Theme Functions
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const theme = savedTheme || 'dark';
    document.body.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Session Functions
function createNewSession() {
    saveCurrentSession();
    const localId = `session-${++sessionCounter}-${Date.now()}`;
    sessions.set(localId, {
        localId,
        serverId: null,
        title: 'New Session',
        messages: ''
    });
    activeSessionId = localId;
    chatMessages.innerHTML = '';
    addWelcome();
    renderSessionList();
}

function switchSession(targetId) {
    if (targetId === activeSessionId) return;
    saveCurrentSession();
    activeSessionId = targetId;
    const session = sessions.get(targetId);
    chatMessages.innerHTML = session.messages || '';
    if (!chatMessages.innerHTML) addWelcome();
    renderSessionList();
    chatInput.focus();
}

function deleteSession(id, event) {
    if (event) event.stopPropagation();
    sessions.delete(id);
    if (sessions.size === 0) {
        createNewSession();
        return;
    }
    if (activeSessionId === id) {
        const remaining = Array.from(sessions.keys());
        activeSessionId = null;
        switchSession(remaining[remaining.length - 1]);
    } else {
        renderSessionList();
    }
}

function saveCurrentSession() {
    if (!activeSessionId) return;
    const session = sessions.get(activeSessionId);
    if (!session) return;
    session.messages = chatMessages.innerHTML;
    if (session.title === 'New Session') {
        const firstUser = chatMessages.querySelector('.message.user .message-content');
        if (firstUser) {
            const text = firstUser.textContent.trim();
            session.title = text.slice(0, 30) + (text.length > 30 ? '...' : '');
        }
    }
}

function renderSessionList() {
    if (!sessionsList) return;
    sessionsList.innerHTML = '';
    for (const [id, session] of sessions) {
        const item = document.createElement('div');
        item.className = `session-item${id === activeSessionId ? ' active' : ''}`;
        item.addEventListener('click', () => switchSession(id));

        const title = document.createElement('span');
        title.className = 'session-title';
        title.textContent = session.title;

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'session-delete';
        deleteBtn.innerHTML = '&times;';
        deleteBtn.setAttribute('aria-label', 'Delete session');
        deleteBtn.addEventListener('click', (e) => deleteSession(id, e));

        item.appendChild(title);
        item.appendChild(deleteBtn);
        sessionsList.appendChild(item);
    }
}

function addWelcome() {
    addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
}

// Chat Functions
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    addMessage(query, 'user');

    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const activeSession = sessions.get(activeSessionId);
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: activeSession ? activeSession.serverId : null
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.detail || `Query failed (${response.status})`);
        }

        const data = await response.json();

        if (activeSession && !activeSession.serverId) {
            activeSession.serverId = data.session_id;
        }

        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

        // Update session title from first user message
        saveCurrentSession();
        renderSessionList();

    } catch (error) {
        loadingMessage.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;

    // Convert markdown to HTML for assistant messages
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);

    let html = `<div class="message-content">${displayContent}</div>`;

    if (sources && sources.length > 0) {
        // Render sources as clickable links
        const sourceItems = sources.map((source, idx) => {
            const title = source.title || source;
            const lesson = source.lesson;
            const link = source.link;
            const label = lesson ? `${title} - Lesson ${lesson}` : title;
            const url = link || `https://developer.anthropic.com`;
            return `<a href="${url}" target="_blank" rel="noopener" class="source-link">${idx + 1}. ${escapeHtml(label)}</a>`;
        }).join('');

        html += `
            <details class="sources-collapsible" open>
                <summary class="sources-header">Sources (${sources.length})</summary>
                <div class="sources-content">${sourceItems}</div>
            </details>
        `;
    }

    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageId;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load course statistics
async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await fetch(`${API_URL}/courses`);
        if (!response.ok) throw new Error('Failed to load course stats');

        const data = await response.json();
        console.log('Course data received:', data);

        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }

        if (courseTitles) {
            if (data.course_titles && data.course_titles.length > 0) {
                courseTitles.innerHTML = data.course_titles
                    .map(title => `<div class="course-title-item">${title}</div>`)
                    .join('');
            } else {
                courseTitles.innerHTML = '<span class="no-courses">No courses available</span>';
            }
        }

    } catch (error) {
        console.error('Error loading course stats:', error);
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            courseTitles.innerHTML = '<span class="error">Failed to load courses</span>';
        }
    }
}
