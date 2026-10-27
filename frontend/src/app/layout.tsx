import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Autonomous Testing Agent",
  description: "Enterprise Autonomous Web Testing Platform powered by Playwright and AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-zinc-950 text-zinc-100 min-h-screen flex antialiased selection:bg-blue-600 selection:text-white`}>
        <Sidebar />
        <main className="flex-1 min-w-0 md:ml-64 min-h-screen flex flex-col bg-zinc-950">
          <div className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
            {children}
          </div>
        </main>
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: "#18181b",
              color: "#f4f4f5",
              border: "1px solid #27272a",
              borderRadius: "10px",
              fontSize: "13px",
            },
          }}
        />
      </body>
    </html>
  );
}

