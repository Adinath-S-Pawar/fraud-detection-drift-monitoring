const BASE_URL = 'http://localhost:8000'

export async function getModelInfo() {
  const res = await fetch(`${BASE_URL}/model-info`)
  return res.json()
}

export async function getPredictions(sortByRisk = false, limit = 50) {
  const res = await fetch(`${BASE_URL}/predictions?sort_by_risk=${sortByRisk}&limit=${limit}`)
  return res.json()
}