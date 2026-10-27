"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export function ChatMessageItem({ role, content, timestamp }: ChatMessageProps) {
  const isAi = role === "assistant";

  return (
    <div
      className={cn(
        "flex w-full gap-3 py-3 px-4 rounded-xl transition-colors",
        isAi ? "bg-zinc-900/60 border border-zinc-800/60" : "bg-transparent ml-auto max-w-2xl justify-end"
      )}
    >
      {isAi && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div className={cn("flex flex-col gap-1 max-w-3xl", !isAi && "items-end")}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-zinc-400">
            {isAi ? "Autonomous Testing Agent" : "You"}
          </span>
          {timestamp && (
            <span className="text-[10px] text-zinc-500">
              {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
        </div>

        <div
          className={cn(
            "text-sm leading-relaxed prose prose-invert max-w-none",
            !isAi && "bg-blue-600 text-white px-4 py-2 rounded-2xl rounded-tr-sm"
          )}
        >
          {isAi ? <ReactMarkdown>{content}</ReactMarkdown> : <p className="m-0">{content}</p>}
        </div>
      </div>

      {!isAi && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
}

