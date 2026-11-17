const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "https://limkobot.onrender.com"
).replace(/\/$/, "");

const TOKEN_KEY = "limkobot_token";
const USER_KEY = "limkobot_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export class ApiError extends Error {
  constructor(status, message, data = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function errorMessage(status, data) {
  if (status === 503) return "Backend database not configured yet.";
  if (status === 413) return "File is too large (10 MB limit).";
  if (data && data.detail) {
    return typeof data.detail === "string"
      ? data.detail
      : JSON.stringify(data.detail);
  }
  return `Request failed (${status})`;
}

/**
 * api(path, { method, body, formData, params, auth })
 * - body: sent as JSON
 * - formData: sent as multipart (do not set Content-Type manually)
 * - params: query string object; empty values are skipped
 * - auth: set false for public calls such as login
 */
export async function api(
  path,
  { method = "GET", body, formData, params, auth = true } = {}
) {
  const url = new URL(BASE_URL + path);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, value);
      }
    });
  }

  const headers = {};
  const token = getToken();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let payload;
  if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(url, { method, headers, body: payload });
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the server. It may be waking up, try again in a moment."
    );
  }

  if (res.status === 401 && auth) {
    clearSession();
    window.location.assign("/login");
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, errorMessage(res.status, data), data);
  }
  return data;
}