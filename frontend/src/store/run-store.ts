import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { TestRun, TestResult, FilterState } from "@/types";
import { testRunsApi } from "@/lib/api";

interface RunStore {
  runs: TestRun[];
  selectedRun: TestRun | null;
  results: TestResult[];
  isLoading: boolean;
  isLoadingResults: boolean;
  filters: FilterState;
  totalResults: number;

  fetchRuns: (projectId?: string) => Promise<void>;
  fetchRun: (id: string) => Promise<void>;
  fetchResults: (runId: string, filters?: FilterState) => Promise<void>;
  setFilters: (filters: Partial<FilterState>) => void;
  updateRun: (run: Partial<TestRun> & { id: string }) => void;
  addResult: (result: TestResult) => void;
  cancelRun: (id: string) => Promise<void>;
}

export const useRunStore = create<RunStore>()(
  devtools(
    (set, get) => ({
      runs: [],
      selectedRun: null,
      results: [],
      isLoading: false,
      isLoadingResults: false,
      filters: { page: 1, pageSize: 20 },
      totalResults: 0,

      fetchRuns: async (projectId?: string) => {
        set({ isLoading: true });
        try {
          const res = await testRunsApi.list(projectId);
          // Backend returns a plain array OR {items:[]} OR {data:[]}
          // Fix operator-precedence: wrap ternary in parens
          const rawRuns: any[] =
            res.data?.items ??
            res.data?.data ??
            (Array.isArray(res.data) ? res.data : []);

          console.log("[RunStore] fetchRuns raw:", rawRuns.length, "runs");

          const runs: TestRun[] = rawRuns.map((r: any) => ({
            id: r.id,
            // Support both snake_case (backend) and camelCase
            projectId: r.project_id ?? r.projectId,
            projectName: r.project_name ?? r.projectName ?? "Web Application",
            status: r.status,
            totalTests: r.total_tests ?? r.totalTests ?? 0,
            passedTests: r.passed ?? r.passedTests ?? 0,
            failedTests: r.failed ?? r.failedTests ?? 0,
            skippedTests: r.skipped ?? r.skippedTests ?? 0,
            duration: r.duration_seconds ?? r.duration,
            createdAt: r.created_at ?? r.createdAt ?? new Date().toISOString(),
            startedAt: r.started_at ?? r.startedAt,
            completedAt: r.completed_at ?? r.completedAt,
            reportPath: r.report_path ?? r.reportPath,
          }));
          set({ runs, isLoading: false });
        } catch (err) {
          console.error("[RunStore] fetchRuns error:", err);
          set({ isLoading: false });
        }
      },


      fetchRun: async (id: string) => {
        set({ isLoading: true });
        try {
          const res = await testRunsApi.get(id);
          const run: TestRun = res.data?.data ?? res.data;
          set({ selectedRun: run, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },

      fetchResults: async (runId: string, filters?: FilterState) => {
        const currentFilters = filters ?? get().filters;
        set({ isLoadingResults: true });
        try {
          const params: Record<string, string | number> = {
            page: currentFilters.page ?? 1,
            page_size: currentFilters.pageSize ?? 20,
          };
          if (currentFilters.status) params.status = currentFilters.status;
          if (currentFilters.category) params.category = currentFilters.category;
          if (currentFilters.search) params.search = currentFilters.search;

          const res = await testRunsApi.getResults(runId, params);
          const results: TestResult[] = res.data?.data ?? res.data ?? [];
          const total: number = res.data?.total ?? results.length;
          set({ results, totalResults: total, isLoadingResults: false });
        } catch {
          set({ isLoadingResults: false });
        }
      },

      setFilters: (filters: Partial<FilterState>) => {
        set((state) => ({ filters: { ...state.filters, ...filters } }));
      },

      updateRun: (run: Partial<TestRun> & { id: string }) => {
        set((state) => ({
          runs: state.runs.map((r) =>
            r.id === run.id ? { ...r, ...run } : r
          ),
          selectedRun:
            state.selectedRun?.id === run.id
              ? { ...state.selectedRun, ...run }
              : state.selectedRun,
        }));
      },

      addResult: (result: TestResult) => {
        set((state) => ({
          results: [result, ...state.results],
          totalResults: state.totalResults + 1,
        }));
      },

      cancelRun: async (id: string) => {
        try {
          await testRunsApi.cancel(id);
          set((state) => ({
            runs: state.runs.map((r) =>
              r.id === id ? { ...r, status: "cancelled" } : r
            ),
            selectedRun:
              state.selectedRun?.id === id
                ? { ...state.selectedRun, status: "cancelled" }
                : state.selectedRun,
          }));
        } catch {
          // handled by interceptor
        }
      },
    }),
    { name: "run-store" }
  )
);
