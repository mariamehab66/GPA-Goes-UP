/**
 * Central API base URL helper.
 *
 * In development the Vite proxy forwards /api/* to Flask at localhost:5000,
 * so VITE_API_URL is empty and all fetch("/api/...") calls work unchanged.
 *
 * In production (Vercel → Render) set VITE_API_URL to the Render service URL
 * in the Vercel dashboard, e.g. https://gpa-goes-up-backend.onrender.com
 * All fetch calls are then resolved against that origin.
 */
export const API_BASE: string = import.meta.env.VITE_API_URL ?? "";

/** Build a full API URL from a path that starts with /api/ */
export const apiUrl = (path: string): string => `${API_BASE}${path}`;
