const BASE_URL = 'http://localhost:8000'

async function safeFetch(url) {
  try {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Server responded with ${res.status}`)
    return await res.json()
  } catch (err) {
    throw new Error('Could not reach the backend. Waiting for API to run...')
  }
}

export async function getModelInfo() {
  return safeFetch(`${BASE_URL}/model-info`)
}

export async function getPredictions(sortByRisk = false, limit = 25, offset = 0) {
  return safeFetch(`${BASE_URL}/predictions?sort_by_risk=${sortByRisk}&limit=${limit}&offset=${offset}`)
}

export async function explainPrediction(id) {
  return safeFetch(`${BASE_URL}/predictions/${id}/explain`)
}

export async function refreshDriftStatus() {
  const res = await fetch(`${BASE_URL}/drift-status/refresh`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to refresh drift status')
  return res.json()
}