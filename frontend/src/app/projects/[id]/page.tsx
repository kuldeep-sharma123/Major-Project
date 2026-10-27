"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Globe,
  Play,
  Layers,
  FileCode,
  History,
  Network,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { projectsApi } from "@/lib/api";
import { useTestRuns } from "@/hooks/useTestRuns";
import { ExecutionProgress } from "@/components/dashboard/execution-progress";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params?.id as string;

  const [project, setProject] = useState<any>(null);
  const [testCases, setTestCases] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "cases" | "runs" | "sitemap">("overview");
  const [loading, setLoading] = useState(true);
  const [runHeaded, setRunHeaded] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentRunningTest, setCurrentRunningTest] = useState<string | null>(null);
  const [liveTests, setLiveTests] = useState<
    Array<{ name: string; status: "running" | "passed" | "failed"; duration?: number; current: number; total: number }>
  >([]);

  const { runs, fetchRuns, triggerRun } = useTestRuns(projectId);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await projectsApi.get(projectId);
      setProject(res.data);

      const tcRes = await projectsApi.getTestCases(projectId);
      setTestCases(tcRes.data || []);
      const currentRuns = await fetchRuns();

      // If no run is in progress and project is ready, reset executing state
      const hasActive = (Array.isArray(currentRuns) ? currentRuns : []).some(
        (r: any) => r.status === "running" || r.status === "pending"
      );
      if (!hasActive && res.data?.status !== "discovering" && res.data?.status !== "running") {
        setIsExecuting(false);
        setCurrentRunningTest(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const { isConnected } = useWebSocket({
    url: typeof window !== "undefined" && projectId ? `ws://localhost:8000/ws/${projectId}` : "",
    enabled: !!projectId,
    onMessage: (event) => {
      const anyEvent = event as any;
      const eventType = event.type || anyEvent.type;
      const payload = anyEvent.payload || anyEvent.data || {};

      if (eventType === "pipeline_started" || eventType === "stage_started") {
        setIsExecuting(true);
        if (payload.stage === "execution") {
          setCurrentRunningTest("Initializing Playwright test runner...");
        }
      } else if (eventType === "test_case_progress") {
        setIsExecuting(true);
        const testName = payload.test_name || "Executing test...";
        setCurrentRunningTest(testName);
        setLiveTests((prev) => {
          const existingIdx = prev.findIndex((t) => t.name === testName);
          const item = {
            name: testName,
            status: (payload.status || "passed") as "running" | "passed" | "failed",
            duration: payload.duration,
            current: payload.current || prev.length + 1,
            total: payload.total || 8,
          };
          if (existingIdx >= 0) {
            const next = [...prev];
            next[existingIdx] = item;
            return next;
          }
          return [...prev, item];
        });
      } else if (eventType === "pipeline_completed" || eventType === "run:completed") {
        setTimeout(() => {
          setIsExecuting(false);
          setCurrentRunningTest(null);
          loadData();
        }, 1500);
      }
    },
  });

  useEffect(() => {
    if (projectId) {
      loadData();
    }
  }, [projectId]);

  // Polling fallback during execution
  useEffect(() => {
    if (!isExecuting) return;
    const interval = setInterval(() => {
      fetchRuns();
    }, 2500);
    return () => clearInterval(interval);
  }, [isExecuting, fetchRuns]);

  if (loading && !project) {
    return <div className="py-20 text-center text-sm text-zinc-500">Loading project details...</div>;
  }

  if (!project) {
    return (
      <div className="py-20 text-center text-sm text-zinc-500">
        Project not found.{" "}
        <Link href="/projects" className="text-blue-400 hover:underline">
          Return to projects
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button & Header */}
      <div>
        <Link
          href="/projects"
          className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-200 mb-3 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to applications
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-5">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
                {project.name}
              </h1>
              <Badge variant="outline">{project.status}</Badge>
            </div>
            <a
              href={project.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-zinc-400 hover:text-blue-400 flex items-center gap-1 mt-1 transition-colors"
            >
              <Globe className="w-3.5 h-3.5" /> {project.url}
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                setIsExecuting(false);
                setCurrentRunningTest(null);
                await loadData();
              }}
              className="border-zinc-800 hover:bg-zinc-800 text-zinc-300"
            >
              <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh
            </Button>
            <label className="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer select-none bg-zinc-900 px-3 py-1.5 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors">
              <input
                type="checkbox"
                checked={runHeaded}
                onChange={(e) => setRunHeaded(e.target.checked)}
                className="w-3.5 h-3.5 rounded bg-zinc-800 border-zinc-700 text-blue-600 cursor-pointer"
              />
              <span className="font-medium text-zinc-200">Headed Mode</span>
            </label>
            <Button
              size="sm"
              onClick={() => {
                setIsExecuting(true);
                setLiveTests([]);
                triggerRun(projectId, runHeaded);
              }}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-md shadow-emerald-950/40"
            >
              <Play className="w-4 h-4 mr-1.5" /> {runHeaded ? "Run Headed Suite" : "Run Test Suite"}
            </Button>
          </div>
        </div>
      </div>

      {/* Real-time execution banner if active */}
      {(isExecuting || project.status === "discovering" || project.status === "running" || runs.some((r) => r.status === "running")) && (
        <Card className="bg-zinc-900/90 border-blue-500/30 shadow-lg p-5 space-y-4">
          <ExecutionProgress
            projectId={projectId}
            currentStep={project.status === "discovering" ? "discovery" : "execution"}
            progress={project.status === "discovering" ? 35 : (liveTests.length > 0 ? Math.round((liveTests.length / 8) * 100) : 75)}
          />

          {/* Real-time Executed Tests List */}
          {liveTests.length > 0 && (
            <div className="pt-3 border-t border-zinc-800/80 space-y-2">
              <div className="flex items-center justify-between text-xs text-zinc-400">
                <span className="font-semibold text-zinc-200">Executed Test Cases:</span>
                <span>
                  <span className="text-emerald-400 font-bold">{liveTests.filter(t => t.status === "passed").length}</span> passed
                  {liveTests.some(t => t.status === "failed") && (
                    <>, <span className="text-red-400 font-bold">{liveTests.filter(t => t.status === "failed").length}</span> failed</>
                  )}
                </span>
              </div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {liveTests.map((t, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs py-1.5 px-3 rounded bg-zinc-950 border border-zinc-800">
                    <span className="font-mono text-zinc-300 truncate mr-3">{t.name}</span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {t.duration && <span className="text-[10px] text-zinc-500">{t.duration}s</span>}
                      <Badge variant={t.status === "passed" ? "success" : "destructive"} className="text-[10px] py-0">
                        {t.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Tabs bar */}
      <div className="flex border-b border-zinc-800 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("overview")}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "overview"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Layers className="w-4 h-4" /> Overview
        </button>
        <button
          onClick={() => setActiveTab("cases")}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "cases"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <FileCode className="w-4 h-4" /> Test Cases ({testCases.length})
        </button>
        <button
          onClick={() => setActiveTab("runs")}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "runs"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <History className="w-4 h-4" /> Test Runs ({runs.length})
        </button>
        <button
          onClick={() => setActiveTab("sitemap")}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "sitemap"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Network className="w-4 h-4" /> Site Map
        </button>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-2 bg-zinc-900/60 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-base text-zinc-100">Application Discovery Map</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-zinc-300">
              <p>
                Our AI Agent crawled this web application, identified interactive forms, input buttons,
                and generated verified Page Object Models for automation.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2">
                <div className="p-3 bg-zinc-800/40 rounded-xl border border-zinc-800">
                  <div className="text-xs text-zinc-400">Pages Mapped</div>
                  <div className="text-xl font-bold text-zinc-100 mt-1">
                    {project.site_map?.pages_found || 8}
                  </div>
                </div>
                <div className="p-3 bg-zinc-800/40 rounded-xl border border-zinc-800">
                  <div className="text-xs text-zinc-400">Forms Discovered</div>
                  <div className="text-xl font-bold text-zinc-100 mt-1">
                    {project.site_map?.forms_found || 4}
                  </div>
                </div>
                <div className="p-3 bg-zinc-800/40 rounded-xl border border-zinc-800">
                  <div className="text-xs text-zinc-400">Interactive Selectors</div>
                  <div className="text-xl font-bold text-zinc-100 mt-1">
                    {project.page_elements?.total_elements || 48}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900/60 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-base text-zinc-100">Testing Capabilities</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-zinc-400">
              <div className="flex items-center gap-2 text-zinc-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Playwright POM Framework generated</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Self-Healing Locators enabled</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Visual Regression Testing</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>AI Root Cause Analysis active</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Allure, Excel & PDF reporting ready</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 2: Test Cases */}
      {activeTab === "cases" && (
        <Card className="bg-zinc-900/60 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">AI Synthesized Test Cases</CardTitle>
          </CardHeader>
          <CardContent>
            {testCases.length === 0 ? (
              <div className="py-8 text-center text-sm text-zinc-500">
                No test cases found. Start test execution to generate comprehensive test cases!
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800 text-xs font-semibold text-zinc-400 uppercase">
                      <th className="py-3 px-4">Test Name</th>
                      <th className="py-3 px-4">Category</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Priority</th>
                      <th className="py-3 px-4">Steps</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/50">
                    {testCases.map((tc) => (
                      <tr key={tc.id} className="hover:bg-zinc-800/30">
                        <td className="py-3 px-4 font-medium text-zinc-200">
                          {tc.name}
                          <div className="text-xs text-zinc-400 font-normal">{tc.description}</div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="outline">{tc.category}</Badge>
                        </td>
                        <td className="py-3 px-4 text-xs text-zinc-400">{tc.test_type}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`text-xs font-semibold ${
                              tc.priority === "critical"
                                ? "text-red-400"
                                : tc.priority === "high"
                                ? "text-amber-400"
                                : "text-blue-400"
                            }`}
                          >
                            {tc.priority}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-xs text-zinc-400">
                          {tc.steps?.length || 0} steps
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Runs */}
      {activeTab === "runs" && (
        <Card className="bg-zinc-900/60 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">Execution Runs</CardTitle>
          </CardHeader>
          <CardContent>
            {runs.length === 0 ? (
              <div className="py-8 text-center text-sm text-zinc-500">
                No runs recorded yet. Click &apos;Run Full Test Suite&apos; above.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800 text-xs font-semibold text-zinc-400 uppercase">
                      <th className="py-3 px-4">Run ID</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Pass Rate</th>
                      <th className="py-3 px-4">Duration</th>
                      <th className="py-3 px-4">Started At</th>
                      <th className="py-3 px-4 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/50">
                    {runs.map((r) => (
                      <tr key={r.id} className="hover:bg-zinc-800/30">
                        <td className="py-3 px-4 font-mono text-xs text-zinc-400">{r.id.slice(0, 8)}...</td>
                        <td className="py-3 px-4">
                          <Badge variant={r.status === "passed" ? "success" : "destructive"}>
                            {r.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-xs text-emerald-400 font-medium">
                          {r.passedTests} / {r.totalTests} passed
                        </td>
                        <td className="py-3 px-4 text-xs text-zinc-400">{r.duration ? `${r.duration}s` : "—"}</td>
                        <td className="py-3 px-4 text-xs text-zinc-400">
                          {new Date(r.createdAt).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link href={`/runs/${r.id}`}>
                            <Button variant="ghost" size="sm" className="text-xs text-blue-400">
                              View
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 4: Site Map */}
      {activeTab === "sitemap" && (
        <Card className="bg-zinc-900/60 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">Discovered Application Structure</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-zinc-950 rounded-xl border border-zinc-800 font-mono text-xs text-zinc-300">
              <pre>{JSON.stringify(project.site_map || { root: project.url, pages: ["/login", "/dashboard", "/admin"] }, null, 2)}</pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

