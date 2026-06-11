import axios from 'axios';
import { supabase } from '../lib/supabase';
import type { ScanResponse, CreditsInfo } from '../types';

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/scan`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120s — first request wakes up Render free tier
});

// Attach auth token to every request if available
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

/**
 * Submit a URL for security scanning.
 * Returns the full scan result including AI summary.
 */
export async function submitScan(url: string): Promise<ScanResponse> {
  const response = await api.post<ScanResponse>('', { url });
  return response.data;
}

/**
 * Retrieve a previously saved scan result by ID.
 */
export async function getScan(id: string): Promise<ScanResponse> {
  const response = await api.get<ScanResponse>(`/${id}`);
  return response.data;
}

/**
 * Fetch live statistics (total scans performed).
 */
export async function getStats(): Promise<{ total_scans: number }> {
  const response = await axios.get<{ total_scans: number }>(
    `${import.meta.env.VITE_API_URL}/scan/stats`,
  );
  return response.data;
}

/**
 * Fetch the authenticated user's scan history.
 */
export async function getHistory(): Promise<ScanResponse[]> {
  const response = await api.get<ScanResponse[]>('/history');
  return response.data;
}

/**
 * Fetch the authenticated user's credit balance.
 */
export async function getCredits(): Promise<CreditsInfo> {
  const response = await api.get<CreditsInfo>('/credits');
  return response.data;
}
