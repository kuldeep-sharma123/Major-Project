import * as React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

export interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  description?: string;
  icon: any;
  trend?: {
    value: number;
    label?: string;
    isPositive?: boolean;
    direction?: "up" | "down" | "neutral";
  };
  iconColor?: string;
  iconBg?: string;
  className?: string;
  isLoading?: boolean;
}

export function StatsCard({
  title,
  value,
  subtitle,
  description,
  icon,
  trend,
  iconColor = "text-blue-400",
  iconBg = "bg-blue-500/10",
  className,
  isLoading = false,
}: StatsCardProps) {
  const direction =
    trend?.direction ??
    (trend?.isPositive === true ? "up" : trend?.isPositive === false ? "down" : "neutral");

  const TrendIcon =
    direction === "up"
      ? TrendingUp
      : direction === "down"
      ? TrendingDown
      : Minus;

  const trendColorClass =
    direction === "up"
      ? "text-emerald-400"
      : direction === "down"
      ? "text-red-400"
      : "text-zinc-400";

  const sub = subtitle || description;

  if (isLoading) {
    return (
      <Card className={cn("p-5", className)}>
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <div className="h-3.5 w-24 bg-zinc-800 rounded shimmer-bg animate-pulse" />
            <div className="h-8 w-20 bg-zinc-800 rounded shimmer-bg animate-pulse" />
            <div className="h-3 w-32 bg-zinc-800 rounded shimmer-bg animate-pulse" />
          </div>
          <div className="w-10 h-10 rounded-lg bg-zinc-800 shimmer-bg animate-pulse" />
        </div>
      </Card>
    );
  }

  const renderIcon = () => {
    if (React.isValidElement(icon)) {
      return icon;
    }
    if (typeof icon === "function" || (typeof icon === "object" && icon !== null)) {
      return React.createElement(icon, { className: "w-5 h-5" });
    }
    return null;
  };

  return (
    <Card
      className={cn(
        "p-5 hover:border-zinc-700 transition-all duration-200 group bg-zinc-900/60 border-zinc-800",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
            {title}
          </p>
          <p className="text-3xl font-bold text-zinc-100 mt-1.5 tabular-nums">
            {value}
          </p>
          {sub && (
            <p className="text-xs text-zinc-500 mt-1 truncate">{sub}</p>
          )}
          {trend && (
            <div className={cn("flex items-center gap-1 mt-2", trendColorClass)}>
              <TrendIcon className="w-3 h-3" />
              <span className="text-xs font-medium">
                {trend.value > 0 ? "+" : ""}
                {trend.value}
                {trend.label && (
                  <span className="text-zinc-500 font-normal ml-1">{trend.label}</span>
                )}
              </span>
            </div>
          )}
        </div>
        <div
          className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ml-4",
            "transition-transform duration-200 group-hover:scale-110",
            iconBg
          )}
        >
          <div className={cn("w-5 h-5 flex items-center justify-center", iconColor)}>
            {renderIcon()}
          </div>
        </div>
      </div>
    </Card>
  );
}
