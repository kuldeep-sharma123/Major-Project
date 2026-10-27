import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  wrapperClassName?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      wrapperClassName,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className={cn("flex flex-col gap-1.5", wrapperClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-zinc-300"
          >
            {label}
            {props.required && (
              <span className="text-red-400 ml-1">*</span>
            )}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3 text-zinc-400 pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              "w-full bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-100",
              "placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-colors duration-200",
              "px-3 py-2.5 h-10",
              leftIcon && "pl-9",
              rightIcon && "pr-9",
              error && "border-red-500 focus:ring-red-500/50 focus:border-red-500",
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 text-zinc-400">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p className="text-xs text-red-400 flex items-center gap-1">
            <span>⚠</span> {error}
          </p>
        )}
        {hint && !error && (
          <p className="text-xs text-zinc-500">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
