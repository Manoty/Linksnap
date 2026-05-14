// api/links.js
import client from './client'

export const linksApi = {
  list:            (params)      => client.get('/api/links/', { params }),
  create:          (data)        => client.post('/api/links/', data),
  shorten:         (data)        => client.post('/api/links/shorten/', data),
  detail:          (shortCode)   => client.get(`/api/links/${shortCode}/`),
  update:          (shortCode, data) => client.patch(`/api/links/${shortCode}/`, data),
  delete:          (shortCode)   => client.delete(`/api/links/${shortCode}/`),
}