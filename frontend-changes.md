# Frontend Changes

## Theme Toggle Feature

### Summary
Added dark/light theme toggle button in top-right corner with sun/moon icons, smooth transitions, keyboard accessibility, and localStorage persistence.

### Files Modified

#### frontend/index.html
- Added `data-theme="dark"` attribute to `<body>` tag
- Added theme toggle button with two SVG icons (sun and moon) positioned before container
- Button includes `aria-label` for accessibility

#### frontend/style.css
- Added light theme CSS variables under `[data-theme="light"]` selector
- Added `transition: background-color 0.3s ease, color 0.3s ease` to `body` for smooth theme switching
- Added `.theme-toggle` button styles:
  - Fixed positioning: `top: 1.5rem; right: 1.5rem; z-index: 1000`
  - Circular shape (44x44px, border-radius: 50%)
  - Hover effect with scale transform
  - Focus ring for keyboard navigation
- Added conditional icon display:
  - Dark theme shows sun icon (switch to light)
  - Light theme shows moon icon (switch to dark)
- Added transitions to all theme-aware elements:
  - `.container`, `.sidebar`, `.chat-container`, `.chat-messages`
  - `.message-content`, `.chat-input-container`, `#chatInput`
  - `.stat-item`, `.suggested-item`

#### frontend/script.js
- Added `initTheme()` function: loads saved theme from localStorage or defaults to 'dark'
- Added `toggleTheme()` function: switches between dark/light and saves to localStorage
- Integrated theme initialization in DOMContentLoaded
- Added click event listener to toggle button

### Accessibility Features
- Button is keyboard-focusable (native button element)
- Focus ring uses `--focus-ring` CSS variable for visibility
- `aria-label="Toggle theme"` for screen readers
- Icon swap provides clear visual feedback

### User Experience
- Smooth 0.3s transitions on all color changes
- Theme preference persists across sessions via localStorage
- Button positioned fixed in top-right for consistent access
- Hover and focus states provide clear interaction feedback

---

## Multi-Session Feature

### Summary
Added multi-session support with session isolation. New sessions can be created via a button in the top-left corner. Sessions are listed in the sidebar and can be switched or deleted. Each session maintains its own chat history independently.

### Files Modified

#### frontend/index.html
- Added "New Session" button with plus icon, positioned top-left (mirrors theme toggle)
- Added "Sessions" section in sidebar above "Courses" section
- Sessions list container `#sessionsList` dynamically populated

#### frontend/style.css
- Added `.new-session-btn` styles:
  - Fixed positioning: `top: 1.5rem; left: 1.5rem; z-index: 1000`
  - Circular shape (44x44px, border-radius: 50%)
  - Hover scale effect, focus ring for keyboard navigation
- Added `.sessions-header` styles (uppercase, matches existing sidebar headers)
- Added `.sessions-list` flex column layout
- Added `.session-item` styles:
  - Hover and active states
  - Active session highlighted with primary color
  - Title truncation with ellipsis
  - Delete button appears on hover with × icon

#### frontend/script.js
- Replaced single `currentSessionId` with multi-session management:
  - `sessions` Map stores all sessions: `{localId, serverId, title, messages}`
  - `activeSessionId` tracks current session
  - `sessionCounter` generates unique local IDs
- Session management functions:
  - `createNewSession()` — creates new session, adds to map, sets active, shows welcome
  - `switchSession(id)` — saves current session state, restores target session
  - `deleteSession(id)` — removes session, switches to another or creates new if empty
  - `saveCurrentSession()` — snapshots chatMessages.innerHTML, updates title from first user message
  - `renderSessionList()` — rebuilds sidebar session list with active highlighting
- Modified `sendMessage()` to use active session's serverId
- Session title auto-updates from first user message (truncated to 30 chars)
- Event listeners: new session button, session item click, delete button click

### Session Isolation
- Each session maintains separate message history in memory
- Switching sessions saves current state and restores target state
- Server-side session IDs tracked per local session
- Sessions persist during page lifetime (in-memory, not localStorage)

### User Experience
- Click "+" button top-left to create new session
- Sessions listed in sidebar with auto-generated titles
- Active session highlighted in primary color
- Click session to switch, hover to reveal delete button
- Each session's chat history completely isolated
- Smooth transitions when switching between sessions
