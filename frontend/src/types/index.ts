/**
 * CryptoScope TypeScript Type Definitions
 * Maps to backend FastAPI models & payloads
 */

export type TargetISA = 'x86-64' | 'ARM32' | 'ARM64' | 'MIPS32-LE' | 'MIPS32-BE' | 'RISC-V 64';
export type CryptoFamily = 'Symmetric Cipher' | 'Asymmetric Cipher' | 'Cryptographic Hash' | 'Message Authentication Code' | 'Non-crypto';
export type CryptoPrimitive = 'AES' | 'DES' | 'RSA' | 'ECC' | 'SHA-256' | 'SHA-512' | 'HMAC' | 'ChaCha20' | 'Non-crypto';

export interface ToolchainInfo {
  name: string;
  target_isa: string;
  command: string;
  installed: boolean;
  version?: string | null;
  path?: string | null;
  install_command: Record<string, string>;
}

export interface ToolchainStatus {
  docker_available: boolean;
  docker_version?: string | null;
  host_os: string;
  tools: ToolchainInfo[];
  ready_isas: string[];
  missing_isas: string[];
  can_compile_local: boolean;
}

export interface FunctionRecord {
  id: string;
  name?: string;
  address: number;
  hex_address: string;
  size: number;
  insn_count: number;
  is_crypto: boolean;
  family: string;
  primitive: string;
  confidence: number;
  is_low_confidence: boolean;
  constants_hit: string[];
  block_count: number;
  cyclomatic_complexity: number;
}

export interface SecurityAdvisory {
  id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFORMATIONAL';
  title: string;
  affected_primitives: string[];
  risk_summary: string;
  remediation_guidance: string;
  cve_references: string[];
}

export interface ProtocolPattern {
  id: string;
  pattern_name: string;
  confidence: number;
  matched_primitives: string[];
  description: string;
  security_caveat: string;
  evidence: string[];
}

export interface ProtocolGraphNode {
  id: string;
  type: string;
  data: {
    label: string;
    primitive: string;
    family: string;
    confidence: number;
    hex_address: string;
  };
  position: { x: number; y: number };
}

export interface ProtocolGraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
}

export interface ProtocolGraphData {
  nodes: ProtocolGraphNode[];
  edges: ProtocolGraphEdge[];
}

export interface AnalysisSummary {
  id: string;
  analysis_id: string;
  filename: string;
  file_size: number;
  sha256: string;
  format: string;
  isa: string;
  endianness: string;
  bits: number;
  entrypoint: string;
  confidence: number;
  total_functions: number;
  primitive_counts: Record<string, number>;
  advisory_count: number;
  pattern_count: number;
}

export interface AnalysisDetail extends AnalysisSummary {
  executable_sections: Array<{
    name: string;
    start: number;
    end: number;
    size: number;
    entropy: number;
  }>;
  functions: FunctionRecord[];
  protocol_graph: ProtocolGraphData;
  patterns: ProtocolPattern[];
  advisories: SecurityAdvisory[];
  call_graph: {
    nodes: Array<{ id: string; label: string }>;
    edges: Array<{ source: string; target: string }>;
  };
}

export interface JobStatus {
  job_id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  step: string;
  message: string;
  logs: string[];
  result_id?: string | null;
  error?: string | null;
}

export interface RunRecord {
  id: string;
  model_type: string;
  dataset_version: string;
  overall_f1: number;
  created_at: string;
  config: Record<string, any>;
  metrics?: {
    level1_metrics?: Record<string, any>;
    level2_metrics?: Record<string, any>;
    level3_metrics?: Record<string, any>;
  };
}

export interface DatasetItem {
  version: string;
  created_at: string;
  binaries_count: number;
  total_functions: number;
  class_distribution: Record<string, number>;
  isa_distribution: Record<string, number>;
  manifest_path: string;
}
