import { 
  ToolchainStatus, 
  AnalysisSummary, 
  AnalysisDetail, 
  JobStatus, 
  RunRecord, 
  DatasetItem 
} from '@/types';

const BASE_URL = '/api';

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchToolchainStatus(): Promise<ToolchainStatus> {
  const res = await fetch(`${BASE_URL}/toolchain/status`);
  if (!res.ok) throw new Error('Failed to fetch toolchain status');
  return res.json();
}

export async function fetchDatasets(): Promise<{ datasets: DatasetItem[] }> {
  const res = await fetch(`${BASE_URL}/datasets`);
  if (!res.ok) throw new Error('Failed to fetch datasets');
  return res.json();
}

export async function buildDataset(version: string = 'v1.0.0'): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${BASE_URL}/datasets/build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version }),
  });
  if (!res.ok) throw new Error('Failed to trigger dataset build');
  return res.json();
}

export async function uploadFirmware(formData: FormData): Promise<{ job_id: string; filename: string }> {
  const res = await fetch(`${BASE_URL}/analyze`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || 'Firmware upload failed');
  }
  return res.json();
}

export async function fetchJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${BASE_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error('Failed to fetch job status');
  return res.json();
}

export async function fetchAnalyses(): Promise<AnalysisSummary[]> {
  const res = await fetch(`${BASE_URL}/analyses`);
  if (!res.ok) throw new Error('Failed to fetch analyses');
  return res.json();
}

export async function fetchAnalysisDetail(analysisId: string): Promise<AnalysisDetail> {
  const res = await fetch(`${BASE_URL}/analyses/${analysisId}`);
  if (!res.ok) throw new Error('Failed to fetch analysis details');
  return res.json();
}

export async function fetchFunctionDisasm(fnId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/functions/${fnId}/disasm`);
  if (!res.ok) throw new Error('Failed to fetch disassembly');
  return res.json();
}

export async function fetchFunctionCfg(fnId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/functions/${fnId}/cfg`);
  if (!res.ok) throw new Error('Failed to fetch CFG');
  return res.json();
}

export async function fetchFunctionDfg(fnId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/functions/${fnId}/dfg`);
  if (!res.ok) throw new Error('Failed to fetch DFG');
  return res.json();
}

export async function fetchFunctionExplain(fnId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/functions/${fnId}/explain`);
  if (!res.ok) throw new Error('Failed to fetch function explainability');
  return res.json();
}

export async function fetchRuns(): Promise<{ runs: RunRecord[] }> {
  const res = await fetch(`${BASE_URL}/runs`);
  if (!res.ok) throw new Error('Failed to fetch runs');
  return res.json();
}

export async function fetchRunDetail(runId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/runs/${runId}`);
  if (!res.ok) throw new Error('Failed to fetch run detail');
  return res.json();
}

export async function triggerTraining(payload: any): Promise<{ job_id: string }> {
  const res = await fetch(`${BASE_URL}/train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to trigger training');
  return res.json();
}

export async function fetchAblation(refresh: boolean = false): Promise<any> {
  const res = await fetch(`${BASE_URL}/ablation?refresh=${refresh}`);
  if (!res.ok) throw new Error('Failed to fetch ablation study');
  return res.json();
}

export async function fetchCrossArch(refresh: boolean = false): Promise<any> {
  const res = await fetch(`${BASE_URL}/cross-arch?refresh=${refresh}`);
  if (!res.ok) throw new Error('Failed to fetch cross-architecture matrix');
  return res.json();
}

export async function fetchRobustness(refresh: boolean = false): Promise<any> {
  const res = await fetch(`${BASE_URL}/robustness?refresh=${refresh}`);
  if (!res.ok) throw new Error('Failed to fetch robustness metrics');
  return res.json();
}

export function getReportDownloadUrl(analysisId: string, format: 'pdf' | 'html' | 'json'): string {
  return `${BASE_URL}/reports/${analysisId}?format=${format}`;
}
