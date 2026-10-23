import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number, decimals: number = 1): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export function formatPercent(val: number): string {
  return (val * 100).toFixed(1) + '%';
}

export function truncateHash(hash: string): string {
  if (!hash || hash.length <= 16) return hash;
  return `${hash.slice(0, 8)}…${hash.slice(-8)}`;
}

export interface PrimitiveMeta {
  tag: string;
  name: string;
  color: string;
  borderColor: string;
  bgColor: string;
}

export const PRIMITIVE_TAGS: Record<string, PrimitiveMeta> = {
  'AES': {
    tag: 'AES',
    name: 'AES',
    color: '#E0714F',
    borderColor: '#E0714F',
    bgColor: 'rgba(224, 113, 79, 0.12)',
  },
  'DES': {
    tag: 'DES',
    name: 'DES / 3DES',
    color: '#B78AC2',
    borderColor: '#B78AC2',
    bgColor: 'rgba(183, 138, 194, 0.12)',
  },
  'RSA': {
    tag: 'RSA',
    name: 'RSA',
    color: '#D4A24C',
    borderColor: '#D4A24C',
    bgColor: 'rgba(212, 162, 76, 0.12)',
  },
  'ECC': {
    tag: 'ECC',
    name: 'ECC',
    color: '#4FB3A5',
    borderColor: '#4FB3A5',
    bgColor: 'rgba(79, 179, 165, 0.12)',
  },
  'SHA-256': {
    tag: 'S256',
    name: 'SHA-256',
    color: '#9DBA4F',
    borderColor: '#9DBA4F',
    bgColor: 'rgba(157, 186, 79, 0.12)',
  },
  'SHA-512': {
    tag: 'S512',
    name: 'SHA-512',
    color: '#6FA66B',
    borderColor: '#6FA66B',
    bgColor: 'rgba(111, 166, 107, 0.12)',
  },
  'HMAC': {
    tag: 'HMC',
    name: 'HMAC',
    color: '#D46A9A',
    borderColor: '#D46A9A',
    bgColor: 'rgba(212, 106, 154, 0.12)',
  },
  'ChaCha20': {
    tag: 'CC20',
    name: 'ChaCha20',
    color: '#8DC9B8',
    borderColor: '#8DC9B8',
    bgColor: 'rgba(141, 201, 184, 0.12)',
  },
  'Non-crypto': {
    tag: 'N/C',
    name: 'Non-crypto',
    color: '#7A766E',
    borderColor: '#5E5B55',
    bgColor: 'rgba(122, 118, 110, 0.10)',
  },
  'Unknown': {
    tag: '?',
    name: 'Unknown',
    color: '#9A968F',
    borderColor: '#3D3D3D',
    bgColor: 'rgba(61, 61, 61, 0.20)',
  },
};

export function getPrimitiveMeta(primitive: string): PrimitiveMeta {
  return PRIMITIVE_TAGS[primitive] || PRIMITIVE_TAGS['Unknown'];
}

export const PRIMITIVE_COLORS: Record<string, string> = {
  'AES': '#E0714F',
  'DES': '#B78AC2',
  'RSA': '#D4A24C',
  'ECC': '#4FB3A5',
  'SHA-256': '#9DBA4F',
  'SHA-512': '#6FA66B',
  'HMAC': '#D46A9A',
  'ChaCha20': '#8DC9B8',
  'Non-crypto': '#7A766E',
  'Unknown': '#3D3D3D',
};

export const PRIMITIVE_BADGE_CLASS: Record<string, string> = {
  'AES': 'bg-[#E0714F]/15 text-[#E0714F] border-[#E0714F]/40',
  'DES': 'bg-[#B78AC2]/15 text-[#B78AC2] border-[#B78AC2]/40',
  'RSA': 'bg-[#D4A24C]/15 text-[#D4A24C] border-[#D4A24C]/40',
  'ECC': 'bg-[#4FB3A5]/15 text-[#4FB3A5] border-[#4FB3A5]/40',
  'SHA-256': 'bg-[#9DBA4F]/15 text-[#9DBA4F] border-[#9DBA4F]/40',
  'SHA-512': 'bg-[#6FA66B]/15 text-[#6FA66B] border-[#6FA66B]/40',
  'HMAC': 'bg-[#D46A9A]/15 text-[#D46A9A] border-[#D46A9A]/40',
  'ChaCha20': 'bg-[#8DC9B8]/15 text-[#8DC9B8] border-[#8DC9B8]/40',
  'Non-crypto': 'bg-[#7A766E]/15 text-[#9A968F] border-[#7A766E]/40',
  'Unknown': 'bg-[#3D3D3D]/20 text-[#9A968F] border-[#3D3D3D]',
};
