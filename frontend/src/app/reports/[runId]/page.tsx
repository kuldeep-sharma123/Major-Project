"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  FileSpreadsheet,
  Download,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { reportsApi, testRunsApi } from "@/lib/api";

export default function ReportDetailPage() {
  const params = useParams();
  const runId = params?.runId as string;

  const [summary, setSummary] = useState<any>(null);
  const [defects, setDefects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadReport() {
      try {
        setLoading(true);
        const [sumRes, defRes] = await Promise.all([
          reportsApi.getSummary(runId),
          reportsApi.getDefects(runId),
        ]);
        setSummary(sumRes.data);
        setDefects(defRes.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    if (runId) {
      loadReport();
    }
  }, [runId]);

  if (loading) {
    return <div className="py-20 text-center text-sm text-zinc-500">Generating report overview...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href={`/runs/${runId}`}
          className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-200 mb-3 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Run Details
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
              Autonomous Quality Audit Report
            </h1>
            <p className="text-xs text-zinc-400 mt-1">
              Project: <span className="text-zinc-200 font-semibold">{summary?.project_name || "Target App"}</span> | Run ID: {runId}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <a
              href={`/api/v1/reports/${runId}/pdf`}
              download
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="sm" variant="outline" className="border-zinc-700 text-zinc-200">
                <FileText className="w-4 h-4 mr-1.5 text-red-400" /> Download PDF
              </Button>
            </a>
            <a
              href={`/api/v1/reports/${runId}/excel`}
              download
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="sm" variant="outline" className="border-zinc-700 text-zinc-200">
                <FileSpreadsheet className="w-4 h-4 mr-1.5 text-emerald-400" /> Download Excel
              </Button>
            </a>
            <a
              href="http://localhost:5050"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="sm" className="bg-blue-600 hover:bg-blue-500 text-white font-medium">
                <ExternalLink className="w-4 h-4 mr-1.5" /> Open Allure Dashboard
              </Button>
            </a>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-zinc-900/60 border-zinc-800 p-4">
          <div className="text-xs text-zinc-400">Total Validations</div>
          <div className="text-2xl font-bold text-zinc-100 mt-1">{summary?.total_tests || 0}</div>
        </Card>
        <Card className="bg-zinc-900/60 border-zinc-800 p-4">
          <div className="text-xs text-zinc-400">Passed Tests</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{summary?.passed || 0}</div>
        </Card>
        <Card className="bg-zinc-900/60 border-zinc-800 p-4">
          <div className="text-xs text-zinc-400">Detected Failures</div>
          <div className="text-2xl font-bold text-red-400 mt-1">{summary?.failed || 0}</div>
        </Card>
        <Card className="bg-zinc-900/60 border-zinc-800 p-4">
          <div className="text-xs text-zinc-400">Pass Rate</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{summary?.pass_rate || 0}%</div>
        </Card>
      </div>

      {/* Defects & Root Cause Analysis */}
      <Card className="bg-zinc-900/60 border-zinc-800">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <CardTitle className="text-base text-zinc-100">
              AI Identified Defects & Remediation Advice
            </CardTitle>
          </div>
          <Badge variant="outline">{defects.length} Issues</Badge>
        </CardHeader>
        <CardContent>
          {defects.length === 0 ? (
            <div className="py-8 text-center text-sm text-zinc-500">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
              No defects detected. All test assertions passed with flying colors!
            </div>
          ) : (
            <div className="space-y-4">
              {defects.map((defect) => (
                <div
                  key={defect.id}
                  className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800 space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-zinc-200 text-sm">{defect.title}</span>
                    <Badge variant={defect.severity === "critical" ? "destructive" : "secondary"}>
                      {defect.severity}
                    </Badge>
                  </div>
                  <div className="text-zinc-400">
                    <strong className="text-zinc-300">Root Cause:</strong> {defect.root_cause || "Element locator timed out during submission"}
                  </div>
                  <div className="text-emerald-400 bg-emerald-950/20 p-2.5 rounded-lg border border-emerald-900/30">
                    <strong className="text-emerald-300">AI Suggested Fix:</strong> {defect.suggested_fix || "Use resilient get_by_role('button', name='Submit')"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

