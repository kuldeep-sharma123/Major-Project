import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "danger" | "success" | "secondary";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantStyles: Record<string, string> = {
  default:
    "bg-blue-600 hover:bg-blue-500 text-white border border-blue-600 hover:border-blue-500 shadow-lg shadow-blue-900/20",
  outline:
    "bg-transparent hover:bg-zinc-800 text-zinc-300 border border-zinc-700 hover:border-zinc-600 hover:text-zinc-100",
  ghost:
    "bg-transparent hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 border border-transparent",
  danger:
    "bg-red-600/10 hover:bg-red-600 text-red-400 hover:text-white border border-red-600/30 hover:border-red-600",
  success:
    "bg-emerald-600/10 hover:bg-emerald-600 text-emerald-400 hover:text-white border border-emerald-600/30 hover:border-emerald-600",
  secondary:
    "bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 hover:border-zinc-600",
};

const sizeStyles: Record<string, string> = {
  sm: "text-xs px-3 py-1.5 h-7 gap-1.5",
  md: "text-sm px-4 py-2 h-9 gap-2",
  lg: "text-base px-6 py-2.5 h-11 gap-2.5",
  icon: "text-sm p-2 h-9 w-9",
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "default",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center font-medium rounded-lg",
          "transition-all duration-200 focus-visible:outline-none",
          "focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
          "cursor-pointer select-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        ) : (
          leftIcon
        )}
        {children}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button };
