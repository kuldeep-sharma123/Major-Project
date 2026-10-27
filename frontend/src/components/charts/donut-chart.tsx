"use client";

import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

interface DonutChartProps {
  passed: number;
  failed: number;
  skipped: number;
}

const COLORS = ["#10b981", "#ef4444", "#f59e0b"];

export function DonutChart({ passed, failed, skipped }: DonutChartProps) {
  const total = passed + failed + skipped;
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0;

  const data = total > 0
    ? [
        { name: "Passed", value: passed },
        { name: "Failed", value: failed },
        { name: "Skipped", value: skipped },
      ]
    : [{ name: "No Tests", value: 1 }];

  return (
    <div className="relative w-full h-56 flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={total > 0 ? 4 : 0}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={total > 0 ? COLORS[index % COLORS.length] : "#27272a"}
                stroke="#18181b"
                strokeWidth={2}
              />
            ))}
          </Pie>
          {total > 0 && (
            <Tooltip
              contentStyle={{
                backgroundColor: "#18181b",
                borderColor: "#27272a",
                borderRadius: "8px",
                color: "#f4f4f5",
              }}
            />
          )}
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute flex flex-col items-center justify-center pointer-events-none">
        <span className="text-2xl font-bold text-zinc-100">{passRate}%</span>
        <span className="text-xs text-zinc-400">
          {total > 0 ? "Pass Rate" : "No Tests"}
        </span>
      </div>
    </div>
  );
}
