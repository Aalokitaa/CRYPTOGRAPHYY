import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, ArrowRight, ShieldAlert, FileText, Plus } from 'lucide-react';
import { fetchAnalyses } from '@/lib/api';
import { formatBytes, truncateHash } from '@/lib/utils';
import { DataTable, ColumnDef } from '@/components/ui/DataTable';
import { FilteredZeroState } from '@/components/ui/StateViews';

interface AnalysisItem {
  id: string;
  filename: string;
  format: string;
  isa: string;
  endianness: string;
  file_size: number;
  sha256: string;
  total_functions: number;
  security_advisories?: any[];
}

export const AnalysesListPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: analyses, isLoading } = useQuery({
    queryKey: ['analyses'],
    queryFn: fetchAnalyses,
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [isaFilter, setIsaFilter] = useState('ALL');

  const filtered = analyses?.filter((a) => {
    const matchesSearch = a.filename.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          a.sha256.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesIsa = isaFilter === 'ALL' || a.isa === isaFilter;
    return matchesSearch && matchesIsa;
  }) || [];

  const columns: ColumnDef<AnalysisItem>[] = [
    {
      key: 'filename',
      label: 'Binary Target',
      width: 220,
      isSticky: true,
      render: (val: string) => (
        <span className="font-bold text-text-primary truncate block" title={val}>
          {val}
        </span>
      ),
    },
    {
      key: 'isa',
      label: 'Format / Architecture',
      width: 180,
      isMono: true,
      render: (_: any, item: AnalysisItem) => (
        <span>
          {item.format} ({item.isa}, {item.endianness})
        </span>
      ),
    },
    {
      key: 'file_size',
      label: 'Size',
      width: 90,
      align: 'right',
      isMono: true,
      render: (val: number) => formatBytes(val),
    },
    {
      key: 'sha256',
      label: 'SHA-256 Digest',
      width: 140,
      isMono: true,
      render: (val: string) => (
        <span className="text-text-secondary truncate block" title={val}>
          {truncateHash(val)}
        </span>
      ),
    },
    {
      key: 'total_functions',
      label: 'Functions',
      width: 90,
      align: 'right',
      isMono: true,
      render: (val: number) => val.toLocaleString(),
    },
    {
      key: 'advisories',
      label: 'Advisories',
      width: 100,
      align: 'center',
      render: (_: any, item: AnalysisItem) => {
        const count = item.security_advisories?.length || 0;
        return count > 0 ? (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-[4px] bg-status-danger/15 text-status-danger font-mono text-[12px] font-bold">
            <ShieldAlert className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>{count}</span>
          </span>
        ) : (
          <span className="text-text-disabled font-mono text-[12px]">-</span>
        );
      },
    },
    {
      key: 'actions',
      label: 'Actions',
      width: 90,
      align: 'right',
      render: (_: any, item: AnalysisItem) => (
        <span className="inline-flex items-center gap-1 text-[12px] text-accent font-mono group-hover:underline">
          <span>Inspect</span>
          <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-default pb-3">
        <div>
          <h1 className="text-[18px] font-bold uppercase tracking-tight text-text-primary">
            Firmware Binary Analyses Catalog
          </h1>
          <p className="text-[12px] text-text-secondary mt-1 font-sans">
            Audit history of reverse-engineered firmware targets and cryptographic identification results.
          </p>
        </div>
        <Link
          to="/analyze"
          className="px-4 py-2 bg-accent text-accent-on font-semibold text-[12px] rounded-[4px] hover:bg-accent-hover transition flex items-center gap-1.5 cursor-pointer min-h-[44px]"
        >
          <Plus className="w-4 h-4" strokeWidth={1.5} />
          <span>New Analysis</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-text-disabled absolute left-3 top-3.5" strokeWidth={1.5} />
          <input
            type="text"
            placeholder="Search by filename or SHA-256..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-bg-surface border border-border-default rounded-[4px] pl-9 pr-3 py-2 text-[12px] text-text-primary placeholder:text-text-disabled outline-none focus:border-accent min-h-[44px]"
          />
        </div>

        <select
          value={isaFilter}
          onChange={(e) => setIsaFilter(e.target.value)}
          className="bg-bg-surface border border-border-default text-text-primary rounded-[4px] px-3 py-2 text-[12px] font-mono outline-none focus:border-accent w-full sm:w-auto min-h-[44px]"
        >
          <option value="ALL">All Architectures</option>
          <option value="x86-64">x86-64</option>
          <option value="ARM32">ARM32</option>
          <option value="ARM64">ARM64</option>
          <option value="MIPS32-LE">MIPS32-LE</option>
          <option value="MIPS32-BE">MIPS32-BE</option>
          <option value="RISC-V 64">RISC-V 64</option>
        </select>
      </div>

      {/* Table / Empty State */}
      {filtered.length === 0 && !isLoading ? (
        <FilteredZeroState
          activeFiltersCount={searchQuery || isaFilter !== 'ALL' ? 1 : 0}
          onResetFilters={() => {
            setSearchQuery('');
            setIsaFilter('ALL');
          }}
        />
      ) : (
        <DataTable
          columns={columns}
          data={filtered}
          onRowClick={(row) => navigate(`/analysis/${row.id}`)}
          emptyMessage={isLoading ? 'Loading analyses...' : 'No analyses found.'}
        />
      )}
    </div>
  );
};
