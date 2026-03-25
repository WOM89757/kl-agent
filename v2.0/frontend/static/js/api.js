/**
 * API Client - centralized API communication layer
 */
const API_BASE = '/api/v1';

const api = {
  async request(method, path, body, isFormData = false) {
    const opts = {
      method,
      headers: isFormData ? {} : { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = isFormData ? body : JSON.stringify(body);

    const res = await fetch(`${API_BASE}${path}`, opts);
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || `HTTP ${res.status}`);
    }
    return data;
  },

  // Documents
  listDocuments(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request('GET', `/documents?${qs}`);
  },
  getDocument(docId) {
    return this.request('GET', `/documents/${docId}`);
  },
  uploadDocument(formData) {
    return this.request('POST', '/documents', formData, true);
  },
  updateDocument(docId, data) {
    return this.request('PATCH', `/documents/${docId}`, data);
  },
  deleteDocument(docId) {
    return this.request('DELETE', `/documents/${docId}`);
  },

  // Chat
  ask(question, topK = 5, imageBase64 = null, mediaType = null) {
    return this.request('POST', '/chat/ask', {
      question,
      top_k: topK,
      image_base64: imageBase64,
      media_type: mediaType,
    });
  },

  // Health
  health() {
    return this.request('GET', '/health');
  },
};
