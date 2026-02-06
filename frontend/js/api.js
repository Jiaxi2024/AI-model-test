/**
 * 前端 API 调用封装模块：fetch 封装、SSE 接收、错误处理
 */

const API_BASE = '/api';

/**
 * 通用 fetch 封装
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  // 如果是 FormData，不设置 Content-Type（浏览器自动处理 boundary）
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  const response = await fetch(url, config);

  if (!response.ok) {
    let errorDetail = `请求失败 (${response.status})`;
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      // 忽略 JSON 解析失败
    }
    throw new Error(errorDetail);
  }

  // 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

/**
 * GET 请求
 */
export async function get(endpoint, params = {}) {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, value);
    }
  }
  const query = searchParams.toString();
  const url = query ? `${endpoint}?${query}` : endpoint;
  return request(url);
}

/**
 * POST 请求
 */
export async function post(endpoint, data) {
  return request(endpoint, {
    method: 'POST',
    body: data instanceof FormData ? data : JSON.stringify(data),
  });
}

/**
 * DELETE 请求
 */
export async function del(endpoint) {
  return request(endpoint, { method: 'DELETE' });
}

/**
 * 上传文件
 */
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  return post('/files/upload', formData);
}

/**
 * SSE 流式连接封装
 * 
 * @param {string} endpoint - API 端点
 * @param {object} body - 请求体（JSON）
 * @param {object} handlers - 事件处理器
 *   - onToken(text): 收到增量文本
 *   - onAudio(audioUrl): 收到音频 URL
 *   - onUsage({input_tokens, output_tokens}): 收到 Token 统计
 *   - onDone(data): 流式结束
 *   - onError(message): 发生错误
 * @returns {AbortController} 可用于取消请求
 */
export function streamSSE(endpoint, body, handlers = {}) {
  const controller = new AbortController();
  const url = `${API_BASE}${endpoint}`;

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        let errorMsg = `请求失败 (${response.status})`;
        try {
          const err = await response.json();
          errorMsg = err.detail || errorMsg;
        } catch { /* ignore */ }
        handlers.onError?.(errorMsg);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';
      let currentData = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          // 流结束时处理最后一个缓冲事件
          if (currentEvent && currentData) {
            _dispatchSSEEvent(currentEvent, currentData, handlers);
          }
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const rawLine of lines) {
          const line = rawLine.replace(/\r$/, ''); // 兼容 \r\n

          if (line === '') {
            // 空行 = 事件分隔符，触发事件分派
            if (currentEvent && currentData) {
              _dispatchSSEEvent(currentEvent, currentData, handlers);
            }
            currentEvent = '';
            currentData = '';
          } else if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            // data 可能有多行（SSE 规范允许多个 data: 行拼接）
            const payload = line.slice(5).trimStart();
            currentData = currentData ? currentData + '\n' + payload : payload;
          }
          // 忽略 id:、retry:、: 开头的注释行（心跳）
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        handlers.onError?.(err.message);
      }
    });

  return controller;
}

/**
 * 分派 SSE 事件到对应的 handler
 */
function _dispatchSSEEvent(eventType, eventData, handlers) {
  try {
    const data = JSON.parse(eventData);
    switch (eventType) {
      case 'token':
        handlers.onToken?.(data.text, data.group);
        break;
      case 'audio':
        handlers.onAudio?.(data.audio_url, data.group);
        break;
      case 'usage':
        handlers.onUsage?.(data, data.group);
        break;
      case 'done':
        handlers.onDone?.(data);
        break;
      case 'error':
        handlers.onError?.(data.message, data.group);
        break;
      case 'progress':
        handlers.onProgress?.(data);
        break;
      case 'result':
        handlers.onResult?.(data);
        break;
    }
  } catch (e) {
    console.warn('[SSE] 解析事件失败:', eventType, eventData, e);
  }
}

// 具体 API 方法
export const models = {
  list: () => get('/models'),
  get: (id) => get(`/models/${id}`),
};

export const inference = {
  create: (body, handlers) => streamSSE('/inference', body, handlers),
};

export const comparison = {
  create: (body, handlers) => streamSSE('/comparison', body, handlers),
};

export const autocomplete = {
  suggest: (text, maxSuggestions = 3) =>
    post('/autocomplete', { text, max_suggestions: maxSuggestions }),
};

export const history = {
  list: (params) => get('/history', params),
  detail: (id) => get(`/history/${id}`),
  remove: (id) => del(`/history/${id}`),
  batchDelete: (data) => post('/history/batch-delete', data),
};

export const statistics = {
  overview: () => get('/statistics/overview'),
  usage: (params) => get('/statistics/usage', params),
};

export const settings = {
  setApiKey: (apiKey) => post('/settings/api-key', { api_key: apiKey }),
  clearApiKey: () => del('/settings/api-key'),
};

export const batch = {
  create: (body) => post('/batch', body),
  get: (id) => get(`/batch/${id}`),
  stream: (id, handlers) => {
    // GET SSE — 使用统一的 SSE 解析逻辑
    const controller = new AbortController();
    const url = `${API_BASE}/batch/${id}/stream`;
    console.log('[Batch SSE] Connecting to:', url);
    
    fetch(url, { signal: controller.signal })
      .then(async (response) => {
        console.log('[Batch SSE] Response status:', response.status);
        if (!response.ok) {
          handlers.onError?.('获取批量进度失败');
          return;
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentEvent = '';
        let currentData = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            if (currentEvent && currentData) {
              _dispatchSSEEvent(currentEvent, currentData, handlers);
            }
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const rawLine of lines) {
            const line = rawLine.replace(/\r$/, '');

            if (line === '') {
              if (currentEvent && currentData) {
                _dispatchSSEEvent(currentEvent, currentData, handlers);
              }
              currentEvent = '';
              currentData = '';
            } else if (line.startsWith('event:')) {
              currentEvent = line.slice(6).trim();
            } else if (line.startsWith('data:')) {
              const payload = line.slice(5).trimStart();
              currentData = currentData ? currentData + '\n' + payload : payload;
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') handlers.onError?.(err.message);
      });

    return controller;
  },
  export: (id, format = 'csv') => {
    window.open(`${API_BASE}/batch/${id}/export?format=${format}`, '_blank');
  },
};
