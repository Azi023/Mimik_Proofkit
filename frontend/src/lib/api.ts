import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add API key to requests (send both headers for compatibility)
api.interceptors.request.use((config) => {
  const apiKey = typeof window !== 'undefined'
    ? localStorage.getItem('proofkit_api_key')
    : null;

  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`;
    config.headers['X-API-Key'] = apiKey;
  }

  return config;
});

// Types
export interface CreateAuditRequest {
  url: string;
  mode?: 'fast' | 'full';
  business_type?: string;
  conversion_goal?: string;
  generate_concept?: boolean;
  webhook_url?: string;
}

export interface AuditResponse {
  audit_id: string;
  status: 'queued' | 'processing' | 'complete' | 'failed';
  url?: string;
  estimated_time_seconds?: number;
  created_at: string;
  completed_at?: string;
  scorecard?: Record<string, number>;
  finding_count?: number;
  report_url?: string;
  error?: string;
}

export interface Finding {
  id: string;
  category: string;
  severity: 'P0' | 'P1' | 'P2' | 'P3';
  title: string;
  summary: string;
  impact: string;
  recommendation: string;
  effort: 'S' | 'M' | 'L';
  tags?: string[];
}

export interface Narrative {
  executive_summary: string;
  quick_wins: string[];
  strategic_priorities: string[];
  category_insights: Record<string, string>;
}

export interface ReportResponse {
  audit_id: string;
  url: string;
  scorecard: Record<string, number>;
  findings: Finding[];
  narrative: Narrative;
  lovable_prompt?: string;
}

export interface AuditListResponse {
  audits: AuditResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface ListAuditsParams {
  limit?: number;
  offset?: number;
  status?: string;
}

// API Functions
export async function createAudit(data: CreateAuditRequest): Promise<AuditResponse> {
  const response = await api.post<AuditResponse>('/audits', data);
  return response.data;
}

export async function getAudit(id: string): Promise<AuditResponse> {
  const response = await api.get<AuditResponse>(`/audits/${id}`);
  return response.data;
}

export async function listAudits(params?: ListAuditsParams): Promise<AuditListResponse> {
  const response = await api.get<AuditListResponse>('/audits', { params });
  return response.data;
}

export async function deleteAudit(id: string): Promise<void> {
  await api.delete(`/audits/${id}`);
}

export async function getAuditReport(id: string): Promise<ReportResponse> {
  const response = await api.get<ReportResponse>(`/audits/${id}/report`);
  return response.data;
}

export async function downloadReportJson(id: string): Promise<Blob> {
  const response = await api.get(`/audits/${id}/report/json`, {
    responseType: 'blob',
  });
  return response.data;
}

export async function downloadReportPdf(id: string): Promise<Blob> {
  const response = await api.get(`/audits/${id}/report/pdf`, {
    responseType: 'blob',
  });
  return response.data;
}

// Health check
export async function checkHealth(): Promise<{ status: string; version: string }> {
  const response = await api.get('/health');
  return response.data;
}

// Set API key
export function setApiKey(key: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('proofkit_api_key', key);
  }
}

// Get API key
export function getApiKey(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('proofkit_api_key');
  }
  return null;
}

// Clear API key
export function clearApiKey(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('proofkit_api_key');
  }
}

export default api;
