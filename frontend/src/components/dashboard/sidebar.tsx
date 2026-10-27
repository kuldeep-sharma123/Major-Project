"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  LayoutDashboard,
  FolderKanban,
  MessageSquareCode,
  FileBarChart2,
  Bot,
  Menu,
  X,
  Zap,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Projects",
    href: "/projects",
    icon: FolderKanban,
  },
  {
    label: "AI Chat",
    href: "/chat",
    icon: MessageSquareCode,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const NavContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-zinc-800">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-900/30 flex-shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-zinc-100 leading-none">AI Test Agent</h1>
          <p className="text-[10px] text-zinc-500 mt-0.5">Autonomous Testing</p>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider px-3 mb-3">
          Navigation
        </p>
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "nav-item group",
                isActive && "active"
              )}
            >
              <Icon
                className={cn(
                  "w-4.5 h-4.5 flex-shrink-0 transition-colors",
                  isActive ? "text-blue-400" : "text-zinc-500 group-hover:text-zinc-300"
                )}
                style={{ width: 18, height: 18 }}
              />
              <span>{item.label}</span>
              {isActive && (
                <ChevronRight
                  className="ml-auto w-4 h-4 text-blue-400/60"
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Status indicator */}
      <div className="px-3 py-4 border-t border-zinc-800">
        <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-40" />
          </div>
          <div>
            <p className="text-xs font-medium text-zinc-300">Agent Online</p>
            <p className="text-[10px] text-zinc-600">Ready to test</p>
          </div>
          <Zap className="ml-auto w-3.5 h-3.5 text-yellow-500/60" />
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-300 hover:text-zinc-100 hover:bg-zinc-700 transition-colors"
      >
        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={cn(
          "lg:hidden fixed top-0 left-0 z-40 h-full w-64 bg-zinc-950 border-r border-zinc-800",
          "transition-transform duration-300",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <NavContent />
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-60 flex-shrink-0 bg-zinc-950 border-r border-zinc-800 h-screen sticky top-0">
        <NavContent />
      </aside>
    </>
  );
}
