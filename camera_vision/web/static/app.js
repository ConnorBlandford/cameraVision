(function () {
  const THEME_KEY = 'cv-theme';
  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    document.querySelectorAll('.theme-toggle [data-theme-set]').forEach((btn) => {
      btn.setAttribute('aria-pressed', btn.dataset.themeSet === t ? 'true' : 'false');
    });
  }
  applyTheme(localStorage.getItem(THEME_KEY) || 'system');
  document.querySelectorAll('.theme-toggle [data-theme-set]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const t = btn.dataset.themeSet;
      localStorage.setItem(THEME_KEY, t);
      applyTheme(t);
    });
  });
})();

window.CV = window.CV || {};
window.CV.api = async function api(url, opts) {
  const res = await fetch(url, Object.assign({ headers: { 'Content-Type': 'application/json' } }, opts || {}));
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
};
