/**
 * api.js — Every call to the FastAPI backend goes through here.
 *
 * The backend address comes from VITE_API_URL in frontend/.env
 * (falls back to http://127.0.0.1:8000).
 */
import { useCallback, useEffect, useState } from "react";

export const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

/** Fetch JSON from the backend. Throws an Error with a human-friendly message. */
export async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new Error(`Cannot reach the backend at ${API_URL}. Is it running? (uvicorn backend.main:app)`);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return data;
}

/**
 * React hook: loads `path` when the component appears.
 * Returns { data, loading, error, reload }.
 */
export function useApi(path) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      setState({ data: await api(path), loading: false, error: null });
    } catch (err) {
      setState({ data: null, loading: false, error: err.message });
    }
  }, [path]);

  useEffect(() => { load(); }, [load]);
  return { ...state, reload: load };
}

/** Load several endpoints at once, e.g. useApiMany({ beds: "/beds", wards: "/wards" }). */
export function useApiMany(paths) {
  const key = JSON.stringify(paths);
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const entries = Object.entries(JSON.parse(key));
      const results = await Promise.all(entries.map(([, p]) => api(p)));
      setState({ data: Object.fromEntries(entries.map(([name], i) => [name, results[i]])), loading: false, error: null });
    } catch (err) {
      setState({ data: null, loading: false, error: err.message });
    }
  }, [key]);

  useEffect(() => { load(); }, [load]);
  return { ...state, reload: load };
}

/** Format a number as money (data is synthetic; currency kept neutral). */
export const money = (n) => Number(n || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** "Aarav Sharma" -> "AS" (initials avatars instead of photos). */
export const initials = (name = "") =>
  name.replace(/^Dr\.?\s+/i, "").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
