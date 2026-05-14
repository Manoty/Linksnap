// api/analytics.js
import client from './client'

export const analyticsApi = {
  dashboard: ()           => client.get('/api/analytics/dashboard/'),
  linkStats: (shortCode)  => client.get(`/api/analytics/links/${shortCode}/`),
  activity:  (limit = 20) => client.get('/api/analytics/activity/', { params: { limit } }),
}