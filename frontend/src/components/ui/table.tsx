"use client";

import * as React from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";

interface Column<T> {
  key: keyof T | string;
  header: string;
  sortable?: boolean;
  className?: string;
  headerClassName?: string;
  render?: (value: unknown, row: T, index: number) => React.ReactNode;
}

interface TableProps<T extends Record<string, unknown>> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
  onRowClick?: (row: T) => void;
  rowClassName?: (row: T) => string;
  className?: string;
  // Pagination
  pagination?: boolean;
  page?: number;
  pageSize?: number;
  total?: number;
  onPageChange?: (page: number) => void;
  // Sorting
  sortKey?: string;
  sortDir?: "asc" | "desc";
  onSort?: (key: string) => void;
}

function Table<T extends Record<string, unknown>>({
  columns,
  data,
  isLoading = false,
  emptyMessage = "No data found",
  emptyIcon,
  onRowClick,
  rowClassName,
  className,
  pagination = false,
  page = 1,
  pageSize = 20,
  total = 0,
  onPageChange,
  sortKey,
  sortDir,
  onSort,
}: TableProps<T>) {
  const totalPages = Math.ceil(total / pageSize);

  const SortIcon = ({ colKey }: { colKey: string }) => {
    if (sortKey !== colKey) return <ChevronsUpDown className="w-3.5 h-3.5 text-zinc-600" />;
    if (sortDir === "asc") return <ChevronUp className="w-3.5 h-3.5 text-blue-400" />;
    return <ChevronDown className="w-3.5 h-3.5 text-blue-400" />;
  };

  const SkeletonRow = () => (
    <tr>
      {columns.map((col, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-zinc-800 rounded shimmer-bg animate-pulse" />
        </td>
      ))}
    </tr>
  );

  return (
    <div className={cn("flex flex-col", className)}>
      <div className="overflow-x-auto rounded-xl border border-zinc-800">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  className={cn(
                    "px-4 py-3 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider whitespace-nowrap",
                    col.sortable && onSort && "cursor-pointer hover:text-zinc-100 select-none",
                    col.headerClassName
                  )}
                  onClick={() => col.sortable && onSort?.(String(col.key))}
                >
                  <div className="flex items-center gap-1.5">
                    {col.header}
                    {col.sortable && onSort && <SortIcon colKey={String(col.key)} />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-16 text-center"
                >
                  <div className="flex flex-col items-center gap-3 text-zinc-500">
                    {emptyIcon ?? (
                      <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center text-2xl">
                        📭
                      </div>
                    )}
                    <p className="text-sm">{emptyMessage}</p>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className={cn(
                    "hover:bg-zinc-800/40 transition-colors",
                    onRowClick && "cursor-pointer",
                    rowClassName?.(row)
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((col) => {
                    const value = row[col.key as keyof T];
                    return (
                      <td
                        key={String(col.key)}
                        className={cn(
                          "px-4 py-3 text-sm text-zinc-300",
                          col.className
                        )}
                      >
                        {col.render
                          ? col.render(value, row, rowIndex)
                          : String(value ?? "—")}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination && total > pageSize && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-zinc-500">
            Showing {Math.min((page - 1) * pageSize + 1, total)}–
            {Math.min(page * pageSize, total)} of {total} results
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => onPageChange?.(page - 1)}
              leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
            >
              Prev
            </Button>
            <span className="text-xs text-zinc-400 px-2">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => onPageChange?.(page + 1)}
              rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export { Table };
export type { Column, TableProps };
