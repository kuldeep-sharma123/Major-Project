"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export interface TrendDataPoint {
  date: string;
  passed: number;
  failed: number;
}

interface TestTrendChartProps {
  data?: TrendDataPoint[];
}

export function TestTrendChart({ data }: TestTrendChartProps) {
  const chartData = data && data.length > 0
    ? data
    : [
        { date: "Run 1", passed: 0, failed: 0 },
        { date: "Run 2", passed: 0, failed: 0 },
        { date: "Run 3", passed: 0, failed: 0 },
      ];

  const hasData = data && data.length > 0 && data.some((d) => d.passed > 0 || d.failed > 0);

  return (
    <div className="relative w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 20, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorPassed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="date" stroke="#71717a" fontSize={12} />
          <YAxis stroke="#71717a" fontSize={12} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              borderColor: "#27272a",
              borderRadius: "8px",
              color: "#f4f4f5",
            }}
          />
          <Area
            type="monotone"
            dataKey="passed"
            stroke="#10b981"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPassed)"
            name="Passed"
          />
          <Area
            type="monotone"
            dataKey="failed"
            stroke="#ef4444"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorFailed)"
            name="Failed"
          />
        </AreaChart>
      </ResponsiveContainer>
      {!hasData && (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-950/30 backdrop-blur-[1px]">
          <span className="text-xs text-zinc-500 bg-zinc-900/80 px-3 py-1.5 rounded-full border border-zinc-800">
            Awaiting test executions to plot trend
          </span>
        </div>
      )}
    </div>
  );
}
