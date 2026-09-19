import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000,
});

// Automatic retry interceptor for transient network hiccups or backend boot delays
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (!config || (config.__retryCount || 0) >= 2) {
      return Promise.reject(error);
    }

    const isNetworkError = !error.response || error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED';
    const isGatewayError = error.response && [502, 503, 504].includes(error.response.status);

    // Only retry idempotent GET requests or initial connection attempts
    if (isNetworkError || isGatewayError) {
      config.__retryCount = (config.__retryCount || 0) + 1;
      const delay = config.__retryCount * 750;
      await new Promise((resolve) => setTimeout(resolve, delay));
      return api(config);
    }

    return Promise.reject(error);
  }
);

export const pingBackend = async () => {
  const response = await api.get('/ping', { timeout: 5000 });
  return response.data;
};

export const collectNews = async (data) => {
  const response = await api.post('/collect-news', data);
  return response.data;
};

export const fetchArticles = async (params = {}) => {
  const response = await api.get('/articles', { params });
  return response.data;
};

export const fetchArticleById = async (id) => {
  const response = await api.get(`/articles/${id}`);
  return response.data;
};

export const fetchSources = async () => {
  const response = await api.get('/sources');
  return response.data;
};

export const fetchSourcesStatus = async () => {
  const response = await api.get('/sources/status');
  return response.data;
};

export const addSource = async (sourceData) => {
  const response = await api.post('/sources', sourceData);
  return response.data;
};

export const fetchUsage = async () => {
  const response = await api.get('/usage');
  return response.data;
};

export const fetchCollectionHistory = async () => {
  const response = await api.get('/collection-history');
  return response.data;
};

export const fetchHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const fetchLastRoutingDecision = async () => {
  const response = await api.get('/routing/last-decision');
  return response.data;
};

export const searchSemantic = async (query, limit = 10, minScore = 0.35, entityFilter = null) => {
  const response = await api.post('/semantic/search', {
    query,
    limit,
    min_score: minScore,
    entity_filter: entityFilter,
  });
  return response.data;
};

export const fetchSimilarArticles = async (articleId, limit = 4) => {
  const response = await api.get(`/semantic/similar/${articleId}`, { params: { limit } });
  return response.data;
};

export const fetchSemanticStatus = async () => {
  const response = await api.get('/semantic/status');
  return response.data;
};

export default api;
