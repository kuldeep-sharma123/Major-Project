import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import type { ChatMessage } from "@/types";
import { chatApi } from "@/lib/api";
import { generateId } from "@/lib/utils";

interface ChatStore {
  messages: ChatMessage[];
  conversationId: string | null;
  isTyping: boolean;
  isLoading: boolean;
  error: string | null;

  sendMessage: (content: string) => Promise<void>;
  fetchHistory: () => Promise<void>;
  clearMessages: () => void;
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void;
  setTyping: (typing: boolean) => void;
}

export const useChatStore = create<ChatStore>()(
  devtools(
    persist(
      (set, get) => ({
        messages: [],
        conversationId: null,
        isTyping: false,
        isLoading: false,
        error: null,

        sendMessage: async (content: string) => {
          const userMessage: ChatMessage = {
            id: generateId(),
            role: "user",
            content,
            timestamp: new Date().toISOString(),
          };

          set((state) => ({
            messages: [...state.messages, userMessage],
            isTyping: true,
            error: null,
          }));

          try {
            const res = await chatApi.sendMessage(
              content,
              get().conversationId ?? undefined
            );
            const data = res.data?.data ?? res.data;

            const assistantMessage: ChatMessage = {
              id: generateId(),
              role: "assistant",
              content: data.message ?? data.response ?? "I received your message.",
              timestamp: new Date().toISOString(),
              metadata: data.metadata,
            };

            set((state) => ({
              messages: [...state.messages, assistantMessage],
              conversationId: data.conversation_id ?? state.conversationId,
              isTyping: false,
            }));
          } catch (err) {
            const errorMessage: ChatMessage = {
              id: generateId(),
              role: "assistant",
              content:
                "Sorry, I couldn't connect to the AI backend. Please check that the server is running.",
              timestamp: new Date().toISOString(),
            };
            set((state) => ({
              messages: [...state.messages, errorMessage],
              isTyping: false,
              error: "Failed to get response",
            }));
          }
        },

        fetchHistory: async () => {
          const { conversationId } = get();
          if (!conversationId) return;
          set({ isLoading: true });
          try {
            const res = await chatApi.getHistory(conversationId);
            const messages: ChatMessage[] = res.data?.data ?? res.data ?? [];
            set({ messages, isLoading: false });
          } catch {
            set({ isLoading: false });
          }
        },

        clearMessages: () => {
          set({ messages: [], conversationId: null, error: null });
        },

        addMessage: (message) => {
          const fullMessage: ChatMessage = {
            id: generateId(),
            timestamp: new Date().toISOString(),
            ...message,
          };
          set((state) => ({ messages: [...state.messages, fullMessage] }));
        },

        setTyping: (typing: boolean) => set({ isTyping: typing }),
      }),
      {
        name: "chat-store",
        partialize: (state) => ({
          messages: state.messages.slice(-50),
          conversationId: state.conversationId,
        }),
      }
    ),
    { name: "chat-store" }
  )
);
