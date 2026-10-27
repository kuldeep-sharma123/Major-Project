"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  FolderKanban,
  Play,
  CheckCircle2,
  AlertTriangle,
  Plus,
  ArrowRight,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { StatsCard } from "@/components/dashboard/stats-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { TestTrendChart } from "@/components/charts/test-trend-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { useProjects } from "@/hooks/useProjects";
import { useTestRuns } from "@/hooks/useTestRuns";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { dashboardApi } from "@/lib/api";

export default function DashboardPage() {
  const { projects, loading: projectsLoading, fetchProjects, createProject } = useProjects();
  const { runs, loading: runsLoading, fetchRuns } = useTestRuns();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectUrl, setNewProjectUrl] = useState("");
  const [isHeaded, setIsHeaded] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dashboardStats, setDashboardStats] = useState<{
    total_projects: number;
    total_runs: number;
    total_passed: number;
    total_failed: number;
    total_tests: number;
    overall_pass_rate: number;
  } | null>(null);

  const loadDashboardStats = useCallback(async () => {
    try {
      const res = await dashboardApi.getStats();
      setDashboardStats(res.data);
      console.log("[Dashboard] Stats loaded:", res.data);
    } catch (err) {
      console.warn("[Dashboard] Stats endpoint not available, using computed values");
    }
  }, []);

  useEffect(() => {
    fetchProjects();
    fetchRuns();
    loadDashboardStats();
  }, [fetchProjects, fetchRuns, loadDashboardStats]);

  const handleRefresh = useCallback(async () => {
    console.log("[Dashboard] Refresh clicked — fetching fresh data...");
    setIsRefreshing(true);
    try {
      await Promise.all([fetchProjects(), fetchRuns(), loadDashboardStats()]);
      console.log("[Dashboard] Refresh complete");
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchProjects, fetchRuns, loadDashboardStats]);


  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName || !newProjectUrl) return;

    setIsSubmitting(true);
    try {
      await createProject({ name: newProjectName, url: newProjectUrl, headed: isHeaded });
      setIsModalOpen(false);
      setNewProjectName("");
      setNewProjectUrl("");
      setIsHeaded(false);
      fetchProjects();
      fetchRuns();
    } catch (err) {
      // Handled in hook/api
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalProjects = dashboardStats?.total_projects ?? projects.length;
  const totalRuns = dashboardStats?.total_runs ?? runs.length;
  const totalPassed = dashboardStats?.total_passed ?? runs.reduce((acc, r) => acc + (r.passedTests || 0), 0);
  const totalFailed = dashboardStats?.total_failed ?? runs.reduce((acc, r) => acc + (r.failedTests || 0), 0);
  const totalSkipped = dashboardStats?.total_skipped ?? runs.reduce((acc, r) => acc + (r.skippedTests || 0), 0);
  const totalTests = dashboardStats?.total_tests ?? (totalPassed + totalFailed + totalSkipped);
  const overallPassRate = dashboardStats?.overall_pass_rate ?? (totalTests > 0 ? Math.round((totalPassed / totalTests) * 100) : 0);

  // Real trend data dynamically mapped from actual executions
  const trendData = runs.length > 0
    ? runs
        .slice(0, 10)
        .reverse()
        .map((r, i) => ({
          date: `Run ${i + 1}`,
          passed: r.passedTests || 0,
          failed: r.failedTests || 0,
        }))
    : undefined;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            Autonomous Testing Command Center
            <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-medium">
              Live
            </span>
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            End-to-end self-discovering and executing AI test automation pipeline.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={isRefreshing}
            onClick={handleRefresh}
            className="border-zinc-800 hover:bg-zinc-800 text-zinc-300 transition-all"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? "animate-spin text-blue-400" : ""}`} />
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
          <Button
            size="sm"
            onClick={() => setIsModalOpen(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white font-medium"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Test Target
          </Button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Active Projects"
          value={totalProjects}
          icon={FolderKanban}
          description="Monitored web apps"
        />
        <StatsCard
          title="Total Executions"
          value={totalRuns}
          icon={Play}
          description="Autonomous test runs"
        />
        <StatsCard
          title="Overall Pass Rate"
          value={`${overallPassRate}%`}
          icon={CheckCircle2}
          description="Across all applications"
        />
        <StatsCard
          title="Identified Defects"
          value={totalFailed}
          icon={AlertTriangle}
          description="AI analyzed issues"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 bg-zinc-900/60 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-base font-semibold text-zinc-100">
                Execution Stability Trends
              </CardTitle>
              <p className="text-xs text-zinc-400 mt-0.5">
                Pass vs Fail count across recent test executions
              </p>
            </div>
            <Sparkles className="w-4 h-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <TestTrendChart data={trendData} />
          </CardContent>
        </Card>

        <Card className="bg-zinc-900/60 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold text-zinc-100">
              Pass / Fail Ratio
            </CardTitle>
            <p className="text-xs text-zinc-400 mt-0.5">
              Aggregate distribution of test outcomes
            </p>
          </CardHeader>
          <CardContent>
            <DonutChart
              passed={totalPassed}
              failed={totalFailed}
              skipped={totalSkipped}
            />
          </CardContent>
        </Card>
      </div>

      {/* Recent Test Runs Section */}
      <Card className="bg-zinc-900/60 border-zinc-800">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-base font-semibold text-zinc-100">
              Recent Autonomous Test Runs
            </CardTitle>
            <p className="text-xs text-zinc-400 mt-0.5">
              History of continuous testing runs across discovered pages
            </p>
          </div>
          <Link
            href="/projects"
            className="text-xs font-medium text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
          >
            View all projects <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </CardHeader>
        <CardContent>
          {runsLoading ? (
            <div className="py-8 text-center text-sm text-zinc-500">Loading test runs...</div>
          ) : runs.length === 0 ? (
            <div className="py-10 text-center flex flex-col items-center justify-center">
              <FolderKanban className="w-8 h-8 text-zinc-600 mb-2" />
              <p className="text-sm text-zinc-300 font-medium">No test executions yet</p>
              <p className="text-xs text-zinc-500 mt-1 max-w-sm">
                Enter an application URL above to let AI automatically crawl, generate tests, and execute!
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-zinc-800/80 text-xs font-semibold text-zinc-400 uppercase">
                    <th className="py-3 px-4">Run ID</th>
                    <th className="py-3 px-4">Target Application</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Passed / Total</th>
                    <th className="py-3 px-4">Duration</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {runs.slice(0, 8).map((run) => {
                    const matchedProj = projects.find((p) => p.id === run.projectId || p.id === (run as any).project_id);
                    const appName = run.projectName || matchedProj?.name || "Target Application";
                    const isPassed = run.status === "passed" || run.status === "completed";
                    const isFailed = run.status === "failed";

                    return (
                      <tr key={run.id} className="hover:bg-zinc-800/30 transition-colors">
                        <td className="py-3.5 px-4 font-mono text-xs text-zinc-400">
                          {run.id.slice(0, 8)}...
                        </td>
                        <td className="py-3.5 px-4 font-medium text-zinc-200">
                          {appName}
                        </td>
                        <td className="py-3.5 px-4">
                          <Badge
                            variant={
                              isPassed
                                ? "success"
                                : isFailed
                                ? "destructive"
                                : "secondary"
                            }
                          >
                            {run.status}
                          </Badge>
                        </td>
                        <td className="py-3.5 px-4 text-zinc-300 text-xs">
                          <span className="text-emerald-400 font-medium">{run.passedTests || 0}</span> /{" "}
                          {run.totalTests || 0}
                        </td>
                        <td className="py-3.5 px-4 text-zinc-400 text-xs">
                          {run.duration ? `${run.duration}s` : "—"}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <Link href={`/runs/${run.id}`}>
                            <Button variant="ghost" size="sm" className="text-xs text-blue-400 hover:text-blue-300">
                              Details
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Project Creation Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Test New Web Application"
        description="Provide the target application URL. The autonomous multi-agent pipeline will crawl, inspect pages, synthesize tests, and execute Playwright scripts."
      >
        <form onSubmit={handleCreateProject} className="space-y-4 pt-2">
          <div>
            <label className="text-xs font-semibold text-zinc-300 block mb-1.5">
              Application Name
            </label>
            <Input
              placeholder="e.g. OrangeHRM, SauceDemo, MyWebApp"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-zinc-300 block mb-1.5">
              Website URL
            </label>
            <Input
              placeholder="https://opensource-demo.orangehrmlive.com"
              value={newProjectUrl}
              onChange={(e) => setNewProjectUrl(e.target.value)}
              type="url"
              required
            />
          </div>
          <div className="flex items-center gap-2.5 p-3 rounded-lg bg-zinc-800/40 border border-zinc-800">
            <input
              type="checkbox"
              id="headed-toggle-dashboard"
              checked={isHeaded}
              onChange={(e) => setIsHeaded(e.target.checked)}
              className="w-4 h-4 rounded bg-zinc-900 border-zinc-700 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <label htmlFor="headed-toggle-dashboard" className="text-xs text-zinc-300 cursor-pointer select-none">
              <span className="font-semibold text-blue-400">Headed Mode</span>: Launch visible Chromium browser window on screen during testing
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting} className="bg-blue-600 hover:bg-blue-500 text-white">
              {isSubmitting ? "Starting Discovery..." : "Launch Autonomous Testing"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
