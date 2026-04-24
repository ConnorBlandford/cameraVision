(function () {
  const form = document.getElementById('new-round-form');
  const newStatus = document.getElementById('new-round-status');
  const workflow = document.getElementById('round-workflow');
  const roundMeta = document.getElementById('round-meta');
  const btnScan = document.getElementById('btn-scan');
  const btnDetect = document.getElementById('btn-detect');
  const btnConfirm = document.getElementById('btn-confirm');
  const btnCancel = document.getElementById('btn-cancel');
  const warning = document.getElementById('unsupported-warning');
  const viewer = document.getElementById('detection-viewer');
  const image = document.getElementById('detection-image');
  const overlay = document.getElementById('detection-overlay');
  const list = document.getElementById('detection-list');
  const result = document.getElementById('round-result');

  let round = null;
  let selected = new Set();

  function renderMeta() {
    if (!round) { roundMeta.textContent = ''; return; }
    roundMeta.textContent = `UUID ${round.uuid} • ${round.target_type} • threshold ${round.confidence_threshold} • status: ${round.status}`;
  }

  function renderDetections() {
    list.innerHTML = '';
    overlay.innerHTML = '';
    if (!round || !round.detections) return;

    const imgRect = image.getBoundingClientRect();
    const natW = image.naturalWidth || imgRect.width;
    const natH = image.naturalHeight || imgRect.height;
    const scaleX = imgRect.width / natW;
    const scaleY = imgRect.height / natH;

    round.detections.forEach((d, i) => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = selected.has(i) ? '' : 'ghost';
      btn.textContent = selected.has(i) ? 'Selected' : 'Not selected';
      btn.setAttribute('aria-pressed', selected.has(i) ? 'true' : 'false');
      btn.addEventListener('click', () => {
        if (selected.has(i)) selected.delete(i); else selected.add(i);
        renderDetections();
      });
      const label = document.createElement('span');
      label.textContent = `#${i + 1} ${d.class_name} ${d.confidence.toFixed(2)}`;
      li.appendChild(btn);
      li.appendChild(label);
      list.appendChild(li);

      const box = document.createElement('div');
      const [x1, y1, x2, y2] = d.bbox;
      box.style.position = 'absolute';
      box.style.left = (x1 * scaleX) + 'px';
      box.style.top = (y1 * scaleY) + 'px';
      box.style.width = ((x2 - x1) * scaleX) + 'px';
      box.style.height = ((y2 - y1) * scaleY) + 'px';
      box.style.border = selected.has(i) ? '3px solid #28a745' : '3px dashed #c04040';
      overlay.appendChild(box);
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const target_type = document.getElementById('target-type').value.trim();
    const confidence = parseFloat(document.getElementById('confidence').value);
    try {
      round = await CV.api('/api/detection/round', { method: 'POST', body: JSON.stringify({ target_type, confidence }) });
      newStatus.textContent = '';
      workflow.hidden = false;
      warning.hidden = round.class_filter_applied;
      btnScan.disabled = false;
      btnDetect.disabled = true;
      btnConfirm.disabled = true;
      viewer.hidden = true;
      result.hidden = true;
      selected = new Set();
      renderMeta();
    } catch (e) { newStatus.textContent = 'Error: ' + e.message; }
  });

  btnScan.addEventListener('click', async () => {
    btnScan.disabled = true;
    try {
      round = await CV.api(`/api/detection/round/${round.uuid}/scan`, { method: 'POST' });
      renderMeta();
      btnDetect.disabled = false;
    } catch (e) { newStatus.textContent = 'Scan error: ' + e.message; btnScan.disabled = false; }
  });

  btnDetect.addEventListener('click', async () => {
    btnDetect.disabled = true;
    try {
      round = await CV.api(`/api/detection/round/${round.uuid}/detect`, { method: 'POST' });
      renderMeta();
      selected = new Set(round.detections.map((d, i) => d.preselected ? i : null).filter(x => x !== null));
      viewer.hidden = false;
      image.src = '/' + round.detection_path.replace(/\\/g, '/') + '?t=' + Date.now();
      image.onload = () => renderDetections();
      btnConfirm.disabled = false;
    } catch (e) { newStatus.textContent = 'Detect error: ' + e.message; btnDetect.disabled = false; }
  });

  btnConfirm.addEventListener('click', async () => {
    btnConfirm.disabled = true;
    try {
      round = await CV.api(`/api/detection/round/${round.uuid}/select`, { method: 'POST', body: JSON.stringify({ selected: Array.from(selected) }) });
      renderMeta();
      result.hidden = false;
      result.innerHTML = `<h3>Round complete</h3>
        <p><a href="/${round.target_path.replace(/\\/g, '/')}" target="_blank">View target image</a></p>`;
    } catch (e) { newStatus.textContent = 'Confirm error: ' + e.message; btnConfirm.disabled = false; }
  });

  btnCancel.addEventListener('click', async () => {
    if (!round) return;
    try {
      round = await CV.api(`/api/detection/round/${round.uuid}/cancel`, { method: 'POST' });
      renderMeta();
      workflow.hidden = true;
      newStatus.textContent = 'Round cancelled.';
      round = null;
    } catch (e) { newStatus.textContent = 'Cancel error: ' + e.message; }
  });

  window.addEventListener('resize', renderDetections);
})();
