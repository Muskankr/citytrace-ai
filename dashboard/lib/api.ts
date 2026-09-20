const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

async function fetchAPI(endpoint: string) {
  const response = await fetch(
    `${API_URL}${endpoint}`
  );

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status}`
    );
  }

  return response.json();
}

export async function getCameras() {
  return fetchAPI("/cameras/");
}

export async function getDetections() {
  return fetchAPI("/detections/");
}

export async function getTrajectories() {
  return fetchAPI("/trajectories/");
}

export async function getAnalytics() {
  return fetchAPI("/analytics/");
}

export async function getAlerts() {
  return fetchAPI("/alerts/");
}

export async function getProcessingStatus(
  jobId: string
) {
  return fetchAPI(
    `/video/status/${jobId}`
  );
}

export function getProcessedVideoUrl() {
  return `${API_URL}/video/result`;
}

export async function getODAnalytics() {
  return fetchAPI("/analytics/od");
}

export async function getODMatrix() {
  return fetchAPI("/analytics/od/matrix");
}

export async function getTrafficHeatmap() {
  return fetchAPI("/analytics/heatmap");
}

export async function getBottlenecks() {
  return fetchAPI("/analytics/bottlenecks");
}