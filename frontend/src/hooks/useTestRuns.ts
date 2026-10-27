"use client";

import { useCallback } from "react";
import { useRunStore } from "@/store/run-store";
import type { FilterState } from "@/types";

export function useTestRuns(projectId?: string) {
  const {
    runs,
    selectedRun,
    results,
    isLoading,
    isLoadingResults,
    filters,
    totalResults,
    fetchRuns,
    fetchRun,
    fetchResults,
    setFilters,
    updateRun,
    addResult,
    cancelRun,
  } = useRunStore();

  const passRate =
    selectedRun && selectedRun.totalTests > 0
      ? Math.round((selectedRun.passedTests / selectedRun.totalTests) * 100)
      : 0;

  const handleFetchRuns = useCallback(() => {
    return fetchRuns(projectId);
  }, [fetchRuns, projectId]);

  const handleFetchResults = useCallback(
    (runId: string, f?: FilterState) => {
      return fetchResults(runId, f);
    },
    [fetchResults]
  );

  const handleSetFilter = useCallback(
    (key: keyof FilterState, value: string | number | undefined) => {
      setFilters({ [key]: value, page: 1 });
    },
    [setFilters]
  );

  const filteredRuns = projectId
    ? runs.filter((r) => r.projectId === projectId)
    : runs;

  return {
    runs: filteredRuns,
    allRuns: runs,
    selectedRun,
    results,
    isLoading,
    loading: isLoading,
    isLoadingResults,
    filters,
    totalResults,
    passRate,
    fetchRuns: handleFetchRuns,
    fetchRun,
    fetchResults: handleFetchResults,
    triggerRun: async (pId: string, headed?: boolean) => {
      try {
        const { testRunsApi } = await import("@/lib/api");
        await testRunsApi.create(pId, headed);
        await handleFetchRuns();
      } catch (e) {
        console.error(e);
      }
    },
    setFilters,
    setFilter: handleSetFilter,
    updateRun,
    addResult,
    cancelRun,
  };
}
