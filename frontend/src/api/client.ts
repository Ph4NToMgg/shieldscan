import axios from 'axios';
import type { ScanResponse } from '../types';

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/scan`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s — scans can take a while
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
