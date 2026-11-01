import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 20000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.investigations)) return data.investigations;
  if (Array.isArray(data?.events)) return data.events;
  return [];
}

export function getErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  }
  if (error?.code === "ECONNABORTED") {
    return "The API request timed out.";
  }
  if (error?.message === "Network Error") {
    return "Unable to reach the StockGuard API. Confirm the backend is running.";
  }
  return "Unable to load data. Check the backend connection.";
}

export default api;
