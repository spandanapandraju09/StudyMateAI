/**
 * Intellix AI Operating System — Global Command Palette (Ctrl+K)
 * Fast keyboard-first search, quick actions, navigation, and prompt triggers.
 */

(function () {
  document.addEventListener('DOMContentLoaded', () => {
    initCommandPalette();
  });

  function initCommandPalette() {
    // Create Command Palette Overlay HTML
    const paletteHtml = `
      <div id="cmdPaletteOverlay" class="cmd-palette-overlay" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(3,7,18,0.85); backdrop-filter:blur(16px); z-index:9999; align-items:flex-start; justify-center:center; padding-top:10vh;">
        <div class="cmd-palette-modal" style="width:100%; max-width:650px; background:rgba(15,23,42,0.95); border:1px solid rgba(0,240,255,0.3); border-radius:20px; box-shadow:0 20px 60px rgba(0,240,255,0.25); overflow:hidden; animation:cmdFadeIn 0.2s ease-out;">
          <div style="display:flex; align-items:center; padding:16px 20px; border-bottom:1px solid rgba(255,255,255,0.1); gap:12px;">
            <span style="font-size:1.3rem;">✨</span>
            <input type="text" id="cmdInput" placeholder="Type a command or search Intellix (Ctrl+K)..." style="flex:1; background:transparent; border:none; color:#fff; font-size:1.05rem; outline:none;" autofocus>
            <kbd style="background:rgba(255,255,255,0.1); color:var(--text2); padding:4px 8px; border-radius:6px; font-size:0.75rem;">ESC</kbd>
          </div>
          <div id="cmdResults" style="max-height:380px; overflow-y:auto; padding:10px;">
            <!-- Commands injected dynamically -->
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', paletteHtml);

    const overlay = document.getElementById('cmdPaletteOverlay');
    const input = document.getElementById('cmdInput');
    const results = document.getElementById('cmdResults');

    const commands = [
      { icon: '💬', title: 'Open Nexus AI Chat', desc: 'Universal AI assistant (Coding, Writing, Math, Translation)', action: () => window.location.href = '/chat.html' },
      { icon: '📚', title: 'Open Nexus Library', desc: 'Manage PDF, DOCX, Code, CSV, PPTX & Excel Documents', action: () => window.location.href = '/library.html' },
      { icon: '🛠️', title: 'Open AI Workspace', desc: 'Canvas, Code Playground, Task Kanban, Sticky Notes', action: () => window.location.href = '/workspace.html' },
      { icon: '📊', title: 'Open Dashboard', desc: 'View 3D Mascot, XP Levels, Heatmaps, and Activity', action: () => window.location.href = '/dashboard.html' },
      { icon: '💻', title: 'Code Playground', desc: 'Run JavaScript & Python code scripts in workspace', action: () => window.location.href = '/workspace.html' },
      { icon: '🎨', title: 'Canvas & Whiteboard', desc: 'Draw diagrams, mind maps, and workflow boards', action: () => window.location.href = '/workspace.html' },
      { icon: '❓', title: 'Generate Quiz', desc: 'Auto-generate interactive MCQ quizzes from library docs', action: () => window.location.href = '/quiz.html' },
      { icon: '🃏', title: 'Review Flashcards', desc: 'Spaced repetition 3D flip card decks', action: () => window.location.href = '/flashcards.html' },
      { icon: '⚙️', title: 'Settings & Memory Controls', desc: 'Manage explicit memory bank, themes & accent colors', action: () => window.location.href = '/settings.html' },
    ];

    function renderCommands(filter = '') {
      const q = filter.toLowerCase().trim();
      const matched = commands.filter(c => c.title.toLowerCase().includes(q) || c.desc.toLowerCase().includes(q));
      if (matched.length === 0) {
        results.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text2);">No commands found</div>';
        return;
      }
      results.innerHTML = matched.map((c, i) => `
        <div class="cmd-item" data-index="${i}" style="display:flex; align-items:center; gap:14px; padding:12px 16px; border-radius:12px; cursor:pointer; transition:background 0.2s;" onclick="executeCmd(${commands.indexOf(c)})">
          <span style="font-size:1.4rem;">${c.icon}</span>
          <div style="flex:1;">
            <div style="color:#fff; font-weight:600; font-size:0.95rem;">${c.title}</div>
            <div style="color:var(--text2); font-size:0.8rem;">${c.desc}</div>
          </div>
          <span style="color:var(--accent); font-size:0.8rem;">↵</span>
        </div>
      `).join('');

      // Add hover effect
      document.querySelectorAll('.cmd-item').forEach(el => {
        el.addEventListener('mouseenter', () => el.style.background = 'rgba(0,240,255,0.1)');
        el.addEventListener('mouseleave', () => el.style.background = 'transparent');
      });
    }

    window.executeCmd = function (index) {
      overlay.style.display = 'none';
      if (commands[index]) commands[index].action();
    };

    // Keyboard Shortcuts Listener (Ctrl+K / Cmd+K)
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        overlay.style.display = 'flex';
        input.focus();
        renderCommands();
      } else if (e.key === 'Escape' && overlay.style.display === 'flex') {
        overlay.style.display = 'none';
      }
    });

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.style.display = 'none';
    });

    input.addEventListener('input', (e) => renderCommands(e.target.value));
  }
})();
