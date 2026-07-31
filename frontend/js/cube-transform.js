/**
 * StudyMate AI — 3D AI Cube & Orbital Feature System
 * Preserves the exact 3D AI Cube design, orbital rings, 5 glass feature spheres,
 * and navbar actions matching the reference UI design.
 */
document.addEventListener('DOMContentLoaded', () => {
  initCubeTransformation();
});

function initCubeTransformation() {
  const token = localStorage.getItem('sm_token');
  let user = null;
  try {
    user = JSON.parse(localStorage.getItem('sm_user') || 'null');
  } catch (e) {
    user = null;
  }

  const isLoggedIn = !!(token && user);

  // 1. Upgrade Navigation Bar Actions when Logged In
  const navActions = document.querySelector('.nav-actions');
  if (navActions && isLoggedIn) {
    const firstName = user.name ? user.name.split(' ')[0] : 'Student';
    navActions.innerHTML = `
      <div class="user-logged-pill">
        <span class="user-status-dot"></span>
        <span class="user-pill-name">👤 ${firstName}</span>
        <a href="/dashboard.html" class="btn-gradient-pill btn-dashboard-hero">
          Dashboard <span>→</span>
        </a>
        <button onclick="logoutUser()" class="btn-logout-icon" title="Logout">🚪</button>
      </div>
    `;
  }

  // 2. Ensure 3D AI Cube Faces always display the clean "AI" design matching reference image
  const aiCube = document.getElementById('ai-cube');
  if (aiCube) {
    // Keep 6 faces cleanly labeled AI with cyan/purple glass borders
    const faces = aiCube.querySelectorAll('.cube-face');
    if (faces.length === 6) {
      faces.forEach(face => {
        if (!face.textContent.trim().startsWith('AI')) {
          face.textContent = 'AI';
        }
      });
    }
  }
}

function logoutUser() {
  localStorage.removeItem('sm_token');
  localStorage.removeItem('sm_user');
  window.location.reload();
}
