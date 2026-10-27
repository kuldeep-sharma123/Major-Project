"use client";

import React, { useRef, useEffect } from "react";
import { Bot, Sparkles, Trash2 } from "lucide-react";
import { ChatMessageItem } from "@/components/chat/chat-message";
import { ChatInput } from "@/components/chat/chat-input";
import { useChatStore } from "@/store/chat-store";
import { Button } from "@/components/ui/button";

export default function ChatPage() {
  const { messages, isTyping, sendMessage, clearMessages } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] max-w-4xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
              Autonomous Testing AI Assistant
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            </h1>
            <p className="text-xs text-zinc-400">
              Instruct the agent to discover apps, run test suites, or analyze defects in natural language.
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearMessages}
            className="text-xs text-zinc-500 hover:text-red-400"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-blue-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-zinc-200">
              What application should we test today?
            </h3>
            <p className="text-xs text-zinc-400 max-w-sm">
              Type <strong className="text-zinc-300">&quot;Test OrangeHRM&quot;</strong> or paste any web URL to automatically crawl, synthesize test cases, and execute autonomous Playwright scripts.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessageItem
              key={msg.id}
              role={msg.role}
              content={msg.content}
              timestamp={msg.timestamp}
            />
          ))
        )}

        {isTyping && (
          <div className="flex items-center gap-2 p-4 text-xs text-zinc-400 bg-zinc-900/40 rounded-xl border border-zinc-800/40 w-fit">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" />
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.2s]" />
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.4s]" />
            <span className="ml-1 text-zinc-400">AI Testing Agent is thinking...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input Box */}
      <div className="pt-2 border-t border-zinc-800/80">
        <ChatInput onSendMessage={sendMessage} isLoading={isTyping} />
      </div>
    </div>
  );
}

