/** Severity level for a scan check */
export type Severity = 'ok' | 'warning' | 'critical';

/** Result of the SSL certificate check */
export interface SSLResult {
  check: string;
  passed: boolean;
  detail: string;
  severity: Severity;
}

/** Result of a single security header check */
export interface HeaderResult {
  check: string;
  name: string;
  passed: boolean;
  detail: string;
  severity: Severity;
}

/** Result of the HTTP→HTTPS redirect check */
export interface RedirectResult {
  check: string;
  passed: boolean;
  detail: string;
  severity: Severity;
}

/** Summary of overall check counts */
export interface ScanSummary {
  total_checks: number;
  passed: number;
  failed: number;
}

/** Combined scan results structure */
export interface ScanResults {
  url: string;
  score: number;
  summary: ScanSummary;
  ssl: SSLResult;
  headers: HeaderResult[];
  redirect: RedirectResult;
}

/** Individual AI explanation for a check */
export interface AIExplanation {
  check_name: string;
  status: string;
  explanation: string;
  fix_suggestion: string;
}

/** AI-generated summary response */
export interface AISummary {
  overall_summary: string;
  explanations: AIExplanation[];
}

/** Full scan response from the API */
export interface ScanResponse {
  id: string;
  url: string;
  score: number;
  results: ScanResults;
  ai_summary: string | null;
  created_at: string;
}
