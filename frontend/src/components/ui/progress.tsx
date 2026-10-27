"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

interface ProgressProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  value?: number;
  max?: number;
  color?: "blue" | "emerald" | "red" | "yellow" | "purple";
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  animated?: boolean;
}

const colorMap = {
  blue: "bg-blue-500",
  emerald: "bg-emerald-500",
  red: "bg-red-500",
  yellow: "bg-yellow-500",
  purple: "bg-purple-500",
};

const sizeMap = {
  sm: "h-1.5",
  md: "h-2.5",
  lg: "h-4",
};

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(
  (
    {
      className,
      value = 0,
      max = 100,
      color = "blue",
      size = "md",
      showLabel = false,
      animated = true,
      ...props
    },
    ref
  ) => {
    const pct = Math.min(100, Math.max(0, (value / max) * 100));

    return (
      <div className="w-full">
        {showLabel && (
          <div className="flex justify-between mb-1">
            <span className="text-xs text-zinc-400">Progress</span>
            <span className="text-xs font-medium text-zinc-200">{Math.round(pct)}%</span>
          </div>
        )}
        <ProgressPrimitive.Root
          ref={ref}
          className={cn(
            "relative overflow-hidden rounded-full bg-zinc-800/60",
            sizeMap[size],
            className
          )}
          value={pct}
          max={100}
          {...props}
        >
          <ProgressPrimitive.Indicator
            className={cn(
              "h-full rounded-full transition-all duration-500 ease-out",
              colorMap[color],
              animated && pct > 0 && pct < 100 && "relative after:absolute after:inset-0 after:rounded-full after:bg-white/20 after:animate-pulse"
            )}
            style={{ width: `${pct}%` }}
          />
        </ProgressPrimitive.Root>
      </div>
    );
  }
);

Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };
