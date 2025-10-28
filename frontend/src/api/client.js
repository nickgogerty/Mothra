/**
 * API Client
 * Clean, predictable interface following Nielsen's consistency heuristic
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for consistent error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMessage = error.response?.data?.detail || error.message || 'An error occurred'
    return Promise.reject(new Error(errorMessage))
  }
)

// Search
export const semanticSearch = async (query, options = {}) => {
  const response = await apiClient.post('/search', {
    query,
    entity_type: options.entityType,
    limit: options.limit || 20,
    similarity_threshold: options.similarityThreshold || 0.5,
  })
  return response.data
}

export const getSearchSuggestions = async (query, limit = 5) => {
  const response = await apiClient.get('/search/suggestions', {
    params: { q: query, limit },
  })
  return response.data
}

// Entities
export const getEntities = async (params = {}) => {
  const response = await apiClient.get('/entities', { params })
  return response.data
}

export const getEntity = async (entityId) => {
  const response = await apiClient.get(`/entities/${entityId}`)
  return response.data
}

export const getEntityTypes = async () => {
  const response = await apiClient.get('/entity-types')
  return response.data
}

// Data Sources
export const getDataSources = async (params = {}) => {
  const response = await apiClient.get('/sources', { params })
  return response.data
}

export const getDataSource = async (sourceId) => {
  const response = await apiClient.get(`/sources/${sourceId}`)
  return response.data
}

// Statistics
export const getStatistics = async () => {
  const response = await apiClient.get('/statistics')
  return response.data
}

export const getStatisticsSummary = async () => {
  const response = await apiClient.get('/statistics/summary')
  return response.data
}

export default apiClient
