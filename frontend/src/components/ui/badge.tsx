import * as React from "react";
import { cn, getStatusBgColor } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: string;
  dot?: boolean;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", dot = false, children, ...props }, ref) => {
    const colorClass = getStatusBgColor(variant);

    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",
          colorClass,
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={cn(
              "w-1.5 h-1.5 rounded-full flex-shrink-0",
              {
                "bg-emerald-400": variant === "passed" || variant === "active",
                "bg-red-400": variant === "failed" || variant === "error" || variant === "critical",
                "bg-blue-400 animate-pulse": variant === "running",
                "bg-yellow-400": variant === "skipped",
                "bg-zinc-400": variant === "pending" || variant === "idle",
                "bg-zinc-500": variant === "cancelled",
                "bg-orange-400": variant === "high",
                "bg-blue-300": variant === "low",
                "bg-yellow-300": variant === "medium",
              }
            )}
          />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";

export { Badge };
