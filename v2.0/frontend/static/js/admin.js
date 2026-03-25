/**
 * Admin interface logic
 */

const adminState = {
  documents: [],
  total: 0,
  page: 1,
  pageSize: 10,
  keyword: '',
  selectedDoc: null,
};

// ===== Init =====
async function initAdmin() {
  await loadStats();
  await loadDocuments();
  setupUpload();
  setupSearch();
  setupModal();
}

// ===== Stats =====
async function loadStats() {
  try {
    const data = await api.listDocuments({ page: 1, page_size: 1 });
    document.getElementById('stat-total').textContent = data.total ?? 0;
  } catch (e) {
    console.error(e);
  }
}

// ===== Load Documents =====
async function loadDocuments() {
  const tbody = document.getElementById('doc-tbody');
  tbody.innerHTML = `<tr><td colspan="6" class="table-empty"><div class="loading-spinner" style="margin:0 auto;"></div></td></tr>`;

  try {
    const data = await api.listDocuments({
      page: adminState.page,
      page_size: adminState.pageSize,
      ...(adminState.keyword ? { keyword: adminState.keyword } : {}),
    });

    adminState.documents = data.items;
    adminState.total = data.total;

    renderTable(data.items);
    renderPagination();
    document.getElementById('stat-total').textContent = data.total;

    // Update chunk stats
    const totalChunks = data.items.reduce((s, d) => s + (d.chunks || 0), 0);
    document.getElementById('stat-chunks').textContent = totalChunks;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="table-empty">
      <div class="table-empty-icon">⚠️</div>加载失败：${escapeHtml(err.message)}
    </td></tr>`;
    showToast('加载文档失败：' + err.message, 'error');
  }
}

function renderTable(docs) {
  const tbody = document.getElementById('doc-tbody');
  if (!docs.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="table-empty">
      <div class="table-empty-icon">📂</div><div>暂无文档，请上传知识库文件</div>
    </td></tr>`;
    return;
  }

  tbody.innerHTML = docs.map((doc) => `
    <tr>
      <td>
        <div style="font-weight:500;">${escapeHtml(doc.file_name)}</div>
        ${doc.description ? `<div class="text-muted" style="font-size:12px;">${escapeHtml(doc.description)}</div>` : ''}
      </td>
      <td><span class="file-type-badge badge-${doc.file_type}">${doc.file_type}</span></td>
      <td>${formatFileSize(doc.file_size)}</td>
      <td>${doc.chunks}</td>
      <td>${formatDate(doc.uploaded_at)}</td>
      <td>
        <div class="action-btns">
          <button class="btn-icon btn-view" title="查看详情" onclick="viewDocument('${doc.doc_id}')">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
          </button>
          <button class="btn-icon btn-delete" title="删除" onclick="confirmDelete('${doc.doc_id}', '${escapeHtml(doc.file_name)}')">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

// ===== Pagination =====
function renderPagination() {
  const totalPages = Math.ceil(adminState.total / adminState.pageSize);
  const container = document.getElementById('pagination');
  const info = document.getElementById('table-info');

  const from = (adminState.page - 1) * adminState.pageSize + 1;
  const to = Math.min(adminState.page * adminState.pageSize, adminState.total);
  info.textContent = adminState.total ? `显示 ${from}-${to}，共 ${adminState.total} 条` : '暂无数据';

  container.innerHTML = '';
  if (totalPages <= 1) return;

  const prevBtn = makePageBtn('‹', adminState.page > 1, () => goPage(adminState.page - 1));
  container.appendChild(prevBtn);

  for (let i = 1; i <= totalPages; i++) {
    if (totalPages > 7 && i > 2 && i < totalPages - 1 && Math.abs(i - adminState.page) > 1) {
      if (i === 3 || i === totalPages - 2) {
        const dots = document.createElement('span');
        dots.textContent = '…';
        dots.style.padding = '0 4px';
        dots.style.color = 'var(--text-muted)';
        container.appendChild(dots);
      }
      continue;
    }
    container.appendChild(makePageBtn(i, true, () => goPage(i), i === adminState.page));
  }

  const nextBtn = makePageBtn('›', adminState.page < totalPages, () => goPage(adminState.page + 1));
  container.appendChild(nextBtn);
}

function makePageBtn(label, enabled, onClick, active = false) {
  const btn = document.createElement('button');
  btn.className = 'page-btn' + (active ? ' active' : '');
  btn.textContent = label;
  btn.disabled = !enabled;
  if (enabled) btn.addEventListener('click', onClick);
  return btn;
}

function goPage(page) {
  adminState.page = page;
  loadDocuments();
}

// ===== Search =====
function setupSearch() {
  const input = document.getElementById('search-input');
  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      adminState.keyword = input.value.trim();
      adminState.page = 1;
      loadDocuments();
    }, 400);
  });
}

// ===== Upload =====
function setupUpload() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  dropZone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) uploadFile(e.target.files[0]);
    fileInput.value = '';
  });

  dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });
}

async function uploadFile(file) {
  const allowed = ['.pdf', '.txt', '.md', '.docx'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast('仅支持 PDF、TXT、MD、DOCX 格式', 'error');
    return;
  }

  const progressWrap = document.getElementById('upload-progress');
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');

  progressWrap.style.display = 'block';
  progressBar.style.width = '20%';
  progressText.textContent = `正在上传 ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);

  try {
    progressBar.style.width = '60%';
    const result = await api.uploadDocument(formData);
    progressBar.style.width = '100%';
    progressText.textContent = `✅ 上传成功：${result.document.file_name}（${result.document.chunks} 个分块）`;
    showToast(`上传成功：${result.document.file_name}`, 'success');
    setTimeout(() => { progressWrap.style.display = 'none'; }, 2000);
    adminState.page = 1;
    await loadDocuments();
    await loadStats();
  } catch (err) {
    progressBar.style.width = '100%';
    progressBar.style.background = 'var(--danger)';
    progressText.textContent = `❌ 上传失败：${err.message}`;
    showToast('上传失败：' + err.message, 'error');
    setTimeout(() => {
      progressWrap.style.display = 'none';
      progressBar.style.background = '';
    }, 3000);
  }
}

// ===== View Doc =====
async function viewDocument(docId) {
  try {
    const doc = await api.getDocument(docId);
    adminState.selectedDoc = doc;

    const body = document.getElementById('detail-body');
    body.innerHTML = `
      <div class="detail-row"><span class="detail-label">文档 ID</span><span class="detail-value text-muted" style="font-size:12px;">${escapeHtml(doc.doc_id)}</span></div>
      <div class="detail-row"><span class="detail-label">文件名</span><span class="detail-value"><strong>${escapeHtml(doc.file_name)}</strong></span></div>
      <div class="detail-row"><span class="detail-label">类型</span><span class="detail-value"><span class="file-type-badge badge-${doc.file_type}">${doc.file_type}</span></span></div>
      <div class="detail-row"><span class="detail-label">文件大小</span><span class="detail-value">${formatFileSize(doc.file_size)}</span></div>
      <div class="detail-row"><span class="detail-label">分块数量</span><span class="detail-value">${doc.chunks}</span></div>
      <div class="detail-row"><span class="detail-label">上传时间</span><span class="detail-value">${formatDate(doc.uploaded_at)}</span></div>
      <div class="detail-row">
        <span class="detail-label">备注</span>
        <span class="detail-value">
          <textarea id="doc-desc" style="width:100%;padding:6px;border:1px solid var(--border);border-radius:6px;resize:vertical;min-height:60px;">${escapeHtml(doc.description || '')}</textarea>
        </span>
      </div>
    `;

    openModal('detail-modal');
  } catch (err) {
    showToast('获取文档详情失败：' + err.message, 'error');
  }
}

async function saveDescription() {
  const doc = adminState.selectedDoc;
  if (!doc) return;
  const desc = document.getElementById('doc-desc')?.value ?? '';
  try {
    await api.updateDocument(doc.doc_id, { description: desc });
    showToast('备注已保存', 'success');
    closeModal('detail-modal');
    loadDocuments();
  } catch (err) {
    showToast('保存失败：' + err.message, 'error');
  }
}

// ===== Delete =====
function confirmDelete(docId, fileName) {
  adminState.selectedDoc = { doc_id: docId, file_name: fileName };
  document.getElementById('delete-file-name').textContent = fileName;
  openModal('delete-modal');
}

async function executeDelete() {
  const doc = adminState.selectedDoc;
  if (!doc) return;

  const btn = document.getElementById('confirm-delete-btn');
  btn.disabled = true;
  btn.textContent = '删除中...';

  try {
    await api.deleteDocument(doc.doc_id);
    showToast(`已删除：${doc.file_name}`, 'success');
    closeModal('delete-modal');
    adminState.page = 1;
    await loadDocuments();
    await loadStats();
  } catch (err) {
    showToast('删除失败：' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '确认删除';
  }
}

// ===== Modal =====
function setupModal() {
  document.querySelectorAll('.modal-overlay').forEach((overlay) => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });
}
function openModal(id) { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

// ===== Toast =====
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(40px)'; toast.style.transition = '.3s'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// ===== Helpers =====
function escapeHtml(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function formatFileSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}
function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

document.addEventListener('DOMContentLoaded', initAdmin);
