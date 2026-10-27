"use client";

import React, { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

const SUGGESTIONS = [
  "Test OrangeHRM",
  "Test SauceDemo",
  "Analyze last run failures",
  "Generate security tests for login",
];

export function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput("");
    }
  };

  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <Sparkles className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
        <span className="text-[11px] font-medium text-zinc-400 flex-shrink-0">Suggestions:</span>
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onSendMessage(suggestion)}
            className="text-[11px] bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 hover:border-zinc-700 rounded-full px-3 py-1 whitespace-nowrap transition-colors"
          >
            {suggestion}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="relative flex items-center">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask AI to test an app or analyze test failures..."
          disabled={isLoading}
          className="w-full bg-zinc-900/90 text-zinc-100 placeholder-zinc-500 text-sm rounded-xl pl-4 pr-24 py-3 border border-zinc-800 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all disabled:opacity-50"
        />
        <div className="absolute right-2 flex items-center">
          <Button
            type="submit"
            size="sm"
            disabled={!input.trim() || isLoading}
            className="h-8 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium"
          >
            {isLoading ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}

