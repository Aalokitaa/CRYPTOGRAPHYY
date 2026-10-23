import React, { useState, useRef, useCallback } from 'react';

export interface ColumnDef<T> {
  key: string;
  label: string;
  width?: number; // pixel width
  minWidth?: number;
  align?: 'left' | 'right' | 'center';
  isSticky?: boolean;
  isMono?: boolean;
  render?: (value: any, row: T, index: number) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  selectedId?: string | number | null;
  onRowClick?: (row: T) => void;
  idKey?: keyof T;
  className?: string;
  emptyMessage?: string;
  emptyAction?: { label: string; onClick: () => void };
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  selectedId,
  onRowClick,
  idKey = 'id' as keyof T,
  className = '',
  emptyMessage = 'No records found',
  emptyAction,
}: DataTableProps<T>) {
  // Column resize state
  const [colWidths, setColWidths] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    columns.forEach((col) => {
      if (col.width) initial[col.key] = col.width;
    });
    return initial;
  });

  const resizingRef = useRef<{ colKey: string; startX: number; startWidth: number } | null>(null);

  const startResize = (colKey: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const currentWidth = colWidths[colKey] || 120;
    resizingRef.current = { colKey, startX: e.clientX, startWidth: currentWidth };

    const onMouseMove = (moveEvent: MouseEvent) => {
      if (!resizingRef.current) return;
      const delta = moveEvent.clientX - resizingRef.current.startX;
      const newWidth = Math.max(60, resizingRef.current.startWidth + delta);
      setColWidths((prev) => ({ ...prev, [colKey]: newWidth }));
    };

    const onMouseUp = () => {
      resizingRef.current = null;
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  if (!data || data.length === 0) {
    return (
      <div className={`border border-border-default bg-bg-surface rounded-[6px] p-8 text-center ${className}`}>
        <p className="text-[12px] font-mono text-text-secondary">{emptyMessage}</p>
        {emptyAction && (
          <button
            onClick={emptyAction.onClick}
            className="mt-3 px-3 py-1.5 rounded-[4px] bg-accent text-accent-on text-[12px] font-mono font-medium hover:bg-accent-hover transition cursor-pointer"
          >
            {emptyAction.label}
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`border border-border-default bg-bg-surface rounded-[6px] overflow-hidden flex flex-col ${className}`}>
      <div className="overflow-x-auto overflow-y-auto max-h-[600px] select-text">
        <table className="w-full border-collapse text-left font-sans text-[12px]">
          {/* Sticky uppercase 12px captions */}
          <thead className="sticky top-0 bg-bg-raised border-b border-border-default z-10 select-none">
            <tr className="h-7 text-[12px] font-mono uppercase tracking-[0.04em] text-text-secondary">
              {columns.map((col, index) => {
                const width = colWidths[col.key] || col.width;
                const isSticky = col.isSticky || index === 0;

                return (
                  <th
                    key={col.key}
                    style={width ? { width: `${width}px`, minWidth: `${col.minWidth || 60}px` } : undefined}
                    className={`relative px-3 py-1 font-semibold whitespace-nowrap bg-bg-raised ${
                      col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                    } ${isSticky ? 'sticky left-0 z-20 shadow-[1px_0_0_0_var(--border-default)]' : ''}`}
                  >
                    <span>{col.label}</span>

                    {/* Column resize handle */}
                    <div
                      onMouseDown={(e) => startResize(col.key, e)}
                      className="absolute right-0 top-0 bottom-0 w-1.5 cursor-col-resize hover:bg-accent select-none group"
                      title="Drag to resize column"
                    >
                      <div className="w-px h-full bg-border-default mx-auto group-hover:bg-accent" />
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>

          {/* 28px dense rows, zebra off, hover and selected row states */}
          <tbody className="divide-y divide-border-default/60">
            {data.map((row, rowIdx) => {
              const rowId = row[idKey] ?? rowIdx;
              const isSelected = selectedId !== undefined && selectedId !== null && selectedId === rowId;

              return (
                <tr
                  key={rowId}
                  onClick={() => onRowClick && onRowClick(row)}
                  className={`h-7 transition-colors ${
                    onRowClick ? 'cursor-pointer' : ''
                  } ${
                    isSelected
                      ? 'bg-bg-raised text-text-primary font-medium border-l-[3px] border-l-accent'
                      : 'bg-bg-surface hover:bg-bg-raised/70 text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {columns.map((col, colIdx) => {
                    const val = row[col.key];
                    const isSticky = col.isSticky || colIdx === 0;
                    const rendered = col.render ? col.render(val, row, rowIdx) : val;

                    return (
                      <td
                        key={col.key}
                        className={`px-3 py-1 whitespace-nowrap truncate ${
                          col.align === 'right'
                            ? 'text-right tabular-nums'
                            : col.align === 'center'
                            ? 'text-center'
                            : 'text-left'
                        } ${col.isMono ? 'font-mono' : ''} ${
                          isSticky
                            ? 'sticky left-0 z-10 bg-inherit shadow-[1px_0_0_0_var(--border-default)] font-mono text-text-primary'
                            : ''
                        }`}
                      >
                        {rendered}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
