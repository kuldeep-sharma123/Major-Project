"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Search,
  BrainCircuit,
  Code2,
  Play,
  FileText,
  CheckCircle2,
  Wifi,
  WifiOff,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useRunStore } from "@/store/run-store";
import type { WebSocketEvent, ExecutionStep } from "@/types";

const STEPS: { key: ExecutionStep; label: string; icon: React.ElementType }[] = [
  { key: "discovery", label: "Discovery", icon: Search },
  { key: "analysis", label: "Analysis", icon: BrainCircuit },
  { key: "generation", label: "Generation", icon: Code2 },
  { key: "execution", label: "Execution", icon: Play },
  { key: "reporting", label: "Report", icon: FileText },
];

export interface ExecutionProgressProps {
  runId?: string;
  projectId?: string;
  currentStep?: ExecutionStep | string;
  progress?: number;
  onComplete?: () => void;
}

export function ExecutionProgress({
  runId,
  projectId,
  currentStep: propCurrentStep,
  progress: propProgress,
  onComplete,
}: ExecutionProgressProps) {
  const { selectedRun, updateRun, addResult } = useRunStore();
  const [liveTest, setLiveTest] = useState<{
    name: string;
    current: number;
    total: number;
    status: string;
  } | null>(null);

  const channel = runId || projectId;
  const wsUrl =
    typeof window !== "undefined" && channel
      ? `ws://localhost:8000/ws/${channel}`
      : "";

  const { isConnected, isConnecting } = useWebSocket({
    url: wsUrl,
    enabled: !!channel,
    onMessage: (event: WebSocketEvent) => {
      const anyEvent = event as any;
      const eventType = event.type || anyEvent.type;
      const payload = (event.payload || anyEvent.data || {}) as any;

      if (eventType === "test_case_progress") {
        setLiveTest({
          name: payload.test_name,
          current: payload.current,
          total: payload.total,
          status: payload.status,
        });
      } else if (eventType === "run:progress") {
        if (runId) {
          updateRun({
            id: runId,
            progress: payload.progress,
            currentStep: payload.current_step,
            passedTests: payload.passed ?? selectedRun?.passedTests ?? 0,
            failedTests: payload.failed ?? selectedRun?.failedTests ?? 0,
            totalTests: payload.total ?? selectedRun?.totalTests ?? 0,
          });
        }
      } else if (eventType === "run:test-result") {
        addResult(payload);
      } else if (eventType === "run:completed" || eventType === "pipeline_completed") {
        if (runId) {
          updateRun({
            id: runId,
            status: "passed",
            progress: 100,
            currentStep: "completed",
          });
        }
        onComplete?.();
      } else if (eventType === "run:failed") {
        if (runId) {
          updateRun({
            id: runId,
            status: "failed",
            progress: 100,
            currentStep: "completed",
          });
        }
        onComplete?.();
      }
    },
  });

  const run = runId && selectedRun?.id === runId ? selectedRun : null;
  const activeStepKey = (run?.currentStep || propCurrentStep || "discovery") as ExecutionStep;
  const currentStepIndex = STEPS.findIndex((s) => s.key === activeStepKey);
  const activeProgress = run?.progress ?? propProgress ?? 0;

  if (run && (run.status === "passed" || run.status === "failed" || run.status === "cancelled")) {
    return null;
  }

  if (!run && !propCurrentStep && propProgress === undefined) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="bg-zinc-900 border border-blue-500/20 rounded-xl p-5"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-sm font-semibold text-zinc-100">
            {run ? "Running Tests" : "Autonomous Discovery & Generation Active"}
          </span>
          {run && run.totalTests > 0 && (
            <span className="text-xs text-zinc-500">
              {run.passedTests + run.failedTests}/{run.totalTests}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {runId && (
            <>
              {isConnecting ? (
                <span className="text-xs text-zinc-500 flex items-center gap-1">
                  <WifiOff className="w-3 h-3" /> Connecting...
                </span>
              ) : isConnected ? (
                <span className="text-xs text-emerald-500 flex items-center gap-1">
                  <Wifi className="w-3 h-3" /> Live
                </span>
              ) : (
                <span className="text-xs text-zinc-500 flex items-center gap-1">
                  <WifiOff className="w-3 h-3" /> Offline
                </span>
              )}
            </>
          )}
          <span className="text-sm font-bold text-blue-400">{activeProgress}%</span>
        </div>
      </div>

      {/* Progress bar */}
      <Progress value={activeProgress} color="blue" size="md" className="mb-5" />

      {/* Steps */}
      <div className="flex items-center gap-1">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          const isDone = currentStepIndex > i;
          const isActive = currentStepIndex === i;
          const isPending = currentStepIndex < i;

          return (
            <div key={step.key} className="flex items-center flex-1">
              <div className="flex flex-col items-center gap-1.5 flex-1">
                <div
                  className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-300",
                    isDone && "bg-emerald-500/20 border border-emerald-500/30",
                    isActive && "bg-blue-500/20 border border-blue-500/40 shadow-lg shadow-blue-900/20",
                    isPending && "bg-zinc-800 border border-zinc-700/50"
                  )}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Icon
                      className={cn(
                        "w-4 h-4",
                        isActive && "text-blue-400 animate-pulse",
                        isPending && "text-zinc-600"
                      )}
                    />
                  )}
                </div>
                <span
                  className={cn(
                    "text-[10px] font-medium",
                    isDone && "text-emerald-400",
                    isActive && "text-blue-400",
                    isPending && "text-zinc-600"
                  )}
                >
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={cn(
                    "h-px flex-1 mx-1 mb-5 transition-colors duration-300",
                    isDone ? "bg-emerald-500/40" : "bg-zinc-700/50"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Live Running Test Indicator */}
      {liveTest && (
        <div className="mt-4 p-2.5 rounded-lg bg-zinc-950/80 border border-blue-500/30 flex items-center justify-between text-xs animate-in fade-in">
          <div className="flex items-center gap-2 truncate mr-3">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-zinc-400 font-medium">Running:</span>
            <span className="font-mono text-zinc-100 font-medium truncate">{liveTest.name}</span>
          </div>
          <span className="text-blue-400 font-semibold bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 whitespace-nowrap">
            {liveTest.current} / {liveTest.total}
          </span>
        </div>
      )}

      {/* Live stats */}
      {run && run.totalTests > 0 && (
        <div className="flex items-center gap-4 mt-4 pt-4 border-t border-zinc-800">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-xs text-zinc-400">
              {run.passedTests} passed
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-xs text-zinc-400">
              {run.failedTests} failed
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-zinc-500" />
            <span className="text-xs text-zinc-400">
              {run.totalTests - run.passedTests - run.failedTests} remaining
            </span>
          </div>
        </div>
      )}
    </motion.div>
  );
}
