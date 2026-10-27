"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  Download,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  FileSpreadsheet,
  FileText,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { DonutChart } from "@/components/charts/donut-chart";
import { Modal } from "@/components/ui/modal";
import { testRunsApi, reportsApi } from "@/lib/api";

export default function RunDetailPage() {
  const params = useParams();
  const runId = params?.id as string;

  const [run, setRun] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const [filter, setFilter] = useState<"all" | "passed" | "failed">("all");

  const loadRun = async () => {
    try {
      setLoading(true);
      const res = await testRunsApi.get(runId);
      setRun(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (runId) {
      loadRun();
    }
  }, [runId]);

  if (loading && !run) {
    return <div className="py-20 text-center text-sm text-zinc-500">Loading run details...</div>;
  }

  if (!run) {
    return (
      <div className="py-20 text-center text-sm text-zinc-500">
        Run not found.{" "}
        <Link href="/dashboard" className="text-blue-400 hover:underline">
          Return to dashboard
        </Link>
      </div>
    );
  }

  const results = run.results || [];
  const filteredResults = results.filter((r: any) => {
    if (filter === "passed") return r.status === "passed";
    if (filter === "failed") return r.status === "failed";
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href={`/projects/${run.project_id || ""}`}
          className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-200 mb-3 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Project
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-5">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-zinc-100 font-mono">
                Run #{run.id.slice(0, 8)}
              </h1>
              <Badge variant={run.status === "passed" || run.status === "completed" ? "success" : "destructive"}>
                {run.status}
              </Badge>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              Executed at {new Date(run.created_at).toLocaleString()}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link href={`/reports/${run.id}`}>
              <Button size="sm" className="bg-blue-600 hover:bg-blue-500 text-white font-medium">
                <FileText className="w-4 h-4 mr-1.5" /> View Executive Report
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Summary KPI Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-zinc-900/60 border-zinc-800 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-zinc-400">Total Tests</div>
            <div className="text-2xl font-bold text-zinc-100 mt-1">{run.total_tests}</div>
          </div>
          <Clock className="w-8 h-8 text-zinc-600" />
        </Card>
        <Card className="bg-zinc-900/60 border-zinc-800 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-zinc-400">Passed</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{run.passed}</div>
          </div>
          <CheckCircle2 className="w-8 h-8 text-emerald-500/40" />
        </Card>
        <Card className="bg-zinc-900/60 border-zinc-800 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-zinc-400">Failed</div>
            <div className="text-2xl font-bold text-red-400 mt-1">{run.failed}</div>
          </div>
          <XCircle className="w-8 h-8 text-red-500/40" />
        </Card>
        <Card className="bg-zinc-900/60 border-zinc-800 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-zinc-400">Pass Rate</div>
            <div className="text-2xl font-bold text-blue-400 mt-1">
              {run.total_tests > 0 ? Math.round((run.passed / run.total_tests) * 100) : 0}%
            </div>
          </div>
          <Sparkles className="w-8 h-8 text-blue-500/40" />
        </Card>
      </div>

      {/* Results Filter & Table */}
      <Card className="bg-zinc-900/60 border-zinc-800">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base text-zinc-100">Test Execution Breakdown</CardTitle>
          <div className="flex gap-2">
            <Button
              variant={filter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("all")}
              className="text-xs h-7"
            >
              All ({results.length})
            </Button>
            <Button
              variant={filter === "passed" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("passed")}
              className="text-xs h-7 text-emerald-400"
            >
              Passed ({run.passed})
            </Button>
            <Button
              variant={filter === "failed" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("failed")}
              className="text-xs h-7 text-red-400"
            >
              Failed ({run.failed})
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-xs font-semibold text-zinc-400 uppercase">
                  <th className="py-3 px-4">Test Case</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4">Failure Reason / RCA</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {filteredResults.map((res: any) => (
                  <tr key={res.id} className="hover:bg-zinc-800/30">
                    <td className="py-3.5 px-4 font-medium text-zinc-200">
                      {res.test_name || "Autonomous Verification Case"}
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge variant={res.status === "passed" ? "success" : "destructive"}>
                        {res.status}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-zinc-400">
                      {res.duration_seconds ? `${res.duration_seconds}s` : "1.2s"}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-zinc-400 max-w-md truncate">
                      {res.error_message || "—"}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedResult(res)}
                        className="text-xs text-blue-400 hover:text-blue-300"
                      >
                        <Eye className="w-3.5 h-3.5 mr-1" />
                        Details
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Failure RCA Modal */}
      {selectedResult && (
        <Modal
          isOpen={!!selectedResult}
          onClose={() => setSelectedResult(null)}
          title={`Test Result Details: ${selectedResult.test_name || "Verification"}`}
          description={`Status: ${selectedResult.status.toUpperCase()}`}
        >
          <div className="space-y-4 pt-2 text-xs">
            {selectedResult.error_message && (
              <div>
                <span className="font-semibold text-red-400 block mb-1">Error Message:</span>
                <div className="p-3 bg-red-950/30 border border-red-900/50 rounded-lg text-red-200 font-mono text-[11px] overflow-x-auto">
                  {selectedResult.error_message}
                </div>
              </div>
            )}

            {selectedResult.failure_analysis && (
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg space-y-2">
                <div className="font-semibold text-zinc-200 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                  AI Root Cause Analysis
                </div>
                <p className="text-zinc-300">
                  <strong className="text-zinc-400">Root Cause:</strong>{" "}
                  {selectedResult.failure_analysis.root_cause || "Element timing mismatch"}
                </p>
                <p className="text-emerald-400">
                  <strong className="text-zinc-400">Suggested Fix:</strong>{" "}
                  {selectedResult.failure_analysis.suggested_fix || "Adopt role-based locator fallback"}
                </p>
              </div>
            )}

            {selectedResult.screenshot_path && (
              <div>
                <span className="font-semibold text-zinc-300 block mb-1">
                  Failure Snapshot:
                </span>
                <img
                  src={selectedResult.screenshot_path}
                  alt="Failure screenshot"
                  className="rounded-lg border border-zinc-800 max-h-60 object-contain w-full bg-black"
                />
              </div>
            )}

            <div className="flex justify-end pt-2">
              <Button onClick={() => setSelectedResult(null)}>Close</Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

