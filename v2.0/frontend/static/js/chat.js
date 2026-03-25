/**
 * Chat interface logic
 */

const chatState = {
  messages: [],
  isLoading: false,
  attachment: null, // { type: 'image'|'video', base64, mediaType, url, name }
};

// DOM refs
const messagesContainer = document.getElementById('messages-container');
const welcomeScreen = document.getElementById('welcome-screen');
const questionInput = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');
const attachmentsPreview = document.getElementById('input-attachments');
const imageBtn = document.getElementById('attach-image-btn');
const videoBtn = document.getElementById('attach-video-btn');
const imageInput = document.getElementById('image-input');
const videoInput = document.getElementById('video-input');

// ===== Init =====
function initChat() {
  questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  questionInput.addEventListener('input', autoResizeTextarea);
  sendBtn.addEventListener('click', sendMessage);
  imageBtn.addEventListener('click', () => imageInput.click());
  videoBtn.addEventListener('click', () => videoInput.click());
  imageInput.addEventListener('change', (e) => handleFileAttach(e.target.files[0], 'image'));
  videoInput.addEventListener('change', (e) => handleFileAttach(e.target.files[0], 'video'));

  // Quick prompts
  document.querySelectorAll('.quick-prompt').forEach((btn) => {
    btn.addEventListener('click', () => {
      questionInput.value = btn.textContent.trim();
      autoResizeTextarea();
      questionInput.focus();
    });
  });
}

function autoResizeTextarea() {
  questionInput.style.height = 'auto';
  questionInput.style.height = Math.min(questionInput.scrollHeight, 160) + 'px';
}

// ===== Attachment =====
function handleFileAttach(file, type) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUrl = e.target.result;
    const base64 = dataUrl.split(',')[1];
    const mediaType = file.type;
    chatState.attachment = { type, base64, mediaType, url: dataUrl, name: file.name };
    renderAttachmentPreview();
  };
  reader.readAsDataURL(file);
}

function renderAttachmentPreview() {
  attachmentsPreview.innerHTML = '';
  if (!chatState.attachment) return;

  const { type, url, name } = chatState.attachment;
  const wrap = document.createElement('div');
  wrap.className = 'attachment-preview';

  if (type === 'image') {
    const img = document.createElement('img');
    img.src = url;
    wrap.appendChild(img);
  } else {
    const label = document.createElement('span');
    label.className = 'file-label';
    label.textContent = `🎬 ${name}`;
    wrap.appendChild(label);
  }

  const removeBtn = document.createElement('button');
  removeBtn.className = 'remove-btn';
  removeBtn.textContent = '×';
  removeBtn.addEventListener('click', clearAttachment);
  wrap.appendChild(removeBtn);
  attachmentsPreview.appendChild(wrap);
}

function clearAttachment() {
  chatState.attachment = null;
  attachmentsPreview.innerHTML = '';
  imageInput.value = '';
  videoInput.value = '';
}

// ===== Send Message =====
async function sendMessage() {
  const text = questionInput.value.trim();
  if (!text || chatState.isLoading) return;

  const attachment = chatState.attachment;

  // Hide welcome screen
  if (welcomeScreen) welcomeScreen.style.display = 'none';

  // Add user message
  addMessage('user', text, attachment);

  // Clear input
  questionInput.value = '';
  autoResizeTextarea();
  clearAttachment();

  // Show typing
  chatState.isLoading = true;
  sendBtn.disabled = true;
  const typingId = addTypingIndicator();

  try {
    const imageBase64 = attachment?.type === 'image' ? attachment.base64 : null;
    const mediaType = attachment?.type === 'image' ? attachment.mediaType : null;

    const result = await api.ask(text, 5, imageBase64, mediaType);

    removeTypingIndicator(typingId);
    addMessage('assistant', result.answer, null, result.sources, result.rewritten_query);
  } catch (err) {
    removeTypingIndicator(typingId);
    addMessage('assistant', `抱歉，请求失败：${err.message}`);
  } finally {
    chatState.isLoading = false;
    sendBtn.disabled = false;
  }
}

// ===== Render Messages =====
function addMessage(role, text, attachment = null, sources = [], rewrittenQuery = null) {
  const id = 'msg-' + Date.now();
  const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

  const msg = document.createElement('div');
  msg.className = `message ${role}`;
  msg.id = id;

  const avatarText = role === 'user' ? '我' : 'AI';
  let attachmentHtml = '';
  if (attachment) {
    if (attachment.type === 'image') {
      attachmentHtml = `<img src="${escapeHtml(attachment.url)}" alt="图片" style="max-width:240px;border-radius:8px;margin-top:6px;">`;
    } else if (attachment.type === 'video') {
      attachmentHtml = `<video src="${escapeHtml(attachment.url)}" controls style="max-width:280px;border-radius:8px;margin-top:6px;"></video>`;
    }
  }

  let sourcesHtml = '';
  if (sources && sources.length > 0) {
    const sourceItems = sources.map((s, i) =>
      `<div class="source-item"><strong>[${i + 1}] ${escapeHtml(s.file_name || '')}</strong> · 分块 ${s.chunk_index ?? '-'}<br>
       <span style="font-size:12px;color:#868e96;">${escapeHtml((s.preview || '').slice(0, 120))}...</span></div>`
    ).join('');
    sourcesHtml = `
      <div class="sources-toggle" onclick="toggleSources('${id}')">📎 ${sources.length} 个参考来源</div>
      <div class="sources-panel" id="sources-${id}">${sourceItems}</div>
    `;
    if (rewrittenQuery) {
      sourcesHtml = `<div style="font-size:12px;color:#868e96;margin-bottom:4px;">🔄 改写查询：${escapeHtml(rewrittenQuery)}</div>` + sourcesHtml;
    }
  }

  msg.innerHTML = `
    <div class="msg-avatar">${avatarText}</div>
    <div class="msg-body">
      <div class="msg-bubble">
        ${attachmentHtml}
        <div class="msg-text">${formatMarkdown(text)}</div>
      </div>
      <div class="msg-time">${time}</div>
      ${sourcesHtml}
    </div>
  `;

  messagesContainer.appendChild(msg);
  scrollToBottom();
  chatState.messages.push({ role, text, time });
}

function addTypingIndicator() {
  const id = 'typing-' + Date.now();
  const el = document.createElement('div');
  el.className = 'message assistant';
  el.id = id;
  el.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-body">
      <div class="msg-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  messagesContainer.appendChild(el);
  scrollToBottom();
  return id;
}

function removeTypingIndicator(id) {
  document.getElementById(id)?.remove();
}

function toggleSources(msgId) {
  const panel = document.getElementById(`sources-${msgId}`);
  if (panel) panel.classList.toggle('open');
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ===== Helpers =====
function escapeHtml(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatMarkdown(text) {
  text = escapeHtml(text);
  // Bold
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Inline code
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Headers
  text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Lists
  text = text.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
  text = text.replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`);
  // Numbered lists
  text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  // Line breaks
  text = text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
  return `<p>${text}</p>`;
}

// New chat
function newChat() {
  chatState.messages = [];
  chatState.attachment = null;
  messagesContainer.innerHTML = '';
  if (welcomeScreen) welcomeScreen.style.display = '';
  clearAttachment();
}

// Init on load
document.addEventListener('DOMContentLoaded', initChat);
