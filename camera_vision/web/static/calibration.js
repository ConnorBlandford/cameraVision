(function () {
  const userInput = document.getElementById('user-name');
  const counts = { left: 0, right: 0 };

  function setStatus(side, text) {
    const el = document.querySelector(`[data-intrinsics-status="${side}"]`);
    if (el) el.textContent = text;
  }

  document.querySelectorAll('[data-intrinsics-capture]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const side = btn.dataset.intrinsicsCapture;
      try {
        const r = await CV.api(`/api/calibration/intrinsics/${side}/capture`, { method: 'POST' });
        counts[side] = r.n_captures;
        setStatus(side, r.accepted ? `Captured (${r.n_captures} total).` : `Not enough corners — move/rotate the board (${r.n_captures} so far).`);
      } catch (e) { setStatus(side, 'Error: ' + e.message); }
    });
  });

  document.querySelectorAll('[data-intrinsics-finalise]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const side = btn.dataset.intrinsicsFinalise;
      const user = (userInput.value || '').trim() || 'unknown';
      if (counts[side] < 3) { setStatus(side, 'Need at least 3 valid captures.'); return; }
      try {
        const r = await CV.api(`/api/calibration/intrinsics/${side}/finalise`, {
          method: 'POST', body: JSON.stringify({ user })
        });
        setStatus(side, `Saved. RMS ${r.rms.toFixed(3)} across ${r.n_captures} captures.`);
      } catch (e) { setStatus(side, 'Error: ' + e.message); }
    });
  });

  document.querySelectorAll('[data-intrinsics-reset]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const side = btn.dataset.intrinsicsReset;
      await CV.api(`/api/calibration/intrinsics/${side}/reset`, { method: 'POST' });
      counts[side] = 0;
      setStatus(side, 'Session reset.');
    });
  });

  const exStatus = document.getElementById('extrinsics-status');
  let exCount = 0;

  const exCapture = document.getElementById('extrinsics-capture');
  if (exCapture) exCapture.addEventListener('click', async () => {
    try {
      const r = await CV.api('/api/calibration/extrinsics/capture', { method: 'POST' });
      exCount = r.n_captures;
      exStatus.textContent = r.accepted ? `Captured pair (${r.n_captures}).` : `Pair rejected — need the board visible in both cameras (${r.n_captures} so far).`;
    } catch (e) { exStatus.textContent = 'Error: ' + e.message; }
  });

  const exFinalise = document.getElementById('extrinsics-finalise');
  if (exFinalise) exFinalise.addEventListener('click', async () => {
    const user = (userInput.value || '').trim() || 'unknown';
    if (exCount < 3) { exStatus.textContent = 'Need at least 3 stereo pairs.'; return; }
    try {
      const r = await CV.api('/api/calibration/extrinsics/finalise', { method: 'POST', body: JSON.stringify({ user }) });
      exStatus.textContent = `Saved. RMS ${r.rms.toFixed(3)}.`;
    } catch (e) { exStatus.textContent = 'Error: ' + e.message; }
  });

  const exReset = document.getElementById('extrinsics-reset');
  if (exReset) exReset.addEventListener('click', async () => {
    await CV.api('/api/calibration/extrinsics/reset', { method: 'POST' });
    exCount = 0;
    exStatus.textContent = 'Session reset.';
  });
})();
