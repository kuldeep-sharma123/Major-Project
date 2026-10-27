"use client";

import React from "react";
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface CategoryData {
  category: string;
  count: number;
}

interface BarChartProps {
  data?: CategoryData[];
}

const defaultData: CategoryData[] = [
  { category: "Functional", count: 24 },
  { category: "UI/Layout", count: 14 },
  { category: "Security", count: 8 },
  { category: "Accessibility", count: 12 },
  { category: "Performance", count: 6 },
];

export function BarChart({ data = defaultData }: BarChartProps) {
  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="category" stroke="#71717a" fontSize={11} />
          <YAxis stroke="#71717a" fontSize={11} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              borderColor: "#27272a",
              borderRadius: "8px",
              color: "#f4f4f5",
            }}
          />
          <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Test Cases" />
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}

