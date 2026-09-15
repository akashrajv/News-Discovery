import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

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

export default api;
