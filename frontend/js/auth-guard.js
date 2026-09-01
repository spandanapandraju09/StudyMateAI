/**
 * StudyMate AI — Frontend Authentication Firewall (Auth Guard)
 * Protects private dashboard pages from unauthenticated access.
 */
(function () {
  'use strict';

  // List of public pages that do NOT require authentication
  const PUBLIC_PAGES = [
    '/',
    '/index.html',
    '/index-premium.html',
    '/login.html',
    '/register.html'
  ];

  const currentPath = window.location.pathname;
  const isPublic = PUBLIC_PAGES.some(p => currentPath === p || currentPath.endsWith(p));

  function getToken() {
    return localStorage.getItem('sm_token');
  }

  function isTokenValid(token) {
    if (!token) return false;
    // Simple validation: ensure token has three parts
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    // Decode payload using base64url (replace URL‑safe chars)
    try {
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const payloadJson = atob(base64);
      const payload = JSON.parse(payloadJson);
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        return false; // Token expired
      }
      return true;
    } catch (_) {
      // If decoding fails, fallback to treating token as valid (optional)
      return true;
    }
  }

  // 1. Initial Access Check
  if (!isPublic) {
    const token = getToken();
    if (!isTokenValid(token)) {
      console.warn('[AuthGuard] Unauthenticated access blocked. Redirecting to login...');
      localStorage.removeItem('sm_token');
      localStorage.removeItem('sm_user');
      const redirectUrl = '/login.html?redirect=' + encodeURIComponent(currentPath);
      window.location.href = redirectUrl;
    }
  }

  // 2. Global Fetch Interceptor for 401 Unauthorized responses
  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await originalFetch.apply(this, args);
    if (response.status === 401 && !isPublic) {
      console.warn('[AuthGuard] 401 Unauthorized detected from API. Redirecting to login...');
      localStorage.removeItem('sm_token');
      localStorage.removeItem('sm_user');
      window.location.href = '/login.html?expired=1';
    }
    return response;
  };
})();
