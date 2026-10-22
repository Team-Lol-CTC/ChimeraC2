/**
 * Mission Control Centralized Configuration
 *
 * Provides dynamic API and WebSocket endpoint URLs configurable
 * via Vite environment variables with safe defaults for local development.
 */

const rawApiUrl = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").trim();

// Normalize base URL by removing any trailing slashes
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, "");
export const API_URL = API_BASE_URL;

function deriveWsUrl(apiUrl) {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL.trim();
  }

  // Derive WebSocket protocol from HTTP/HTTPS protocol
  if (apiUrl.startsWith("https://")) {
    return `${apiUrl.replace(/^https:\/\//i, "wss://")}/ws/operator`;
  }
  if (apiUrl.startsWith("http://")) {
    return `${apiUrl.replace(/^http:\/\//i, "ws://")}/ws/operator`;
  }

  return `ws://${apiUrl}/ws/operator`;
}

export const WS_URL = deriveWsUrl(API_BASE_URL);

export default {
  API_BASE_URL,
  API_URL,
  WS_URL,
};
