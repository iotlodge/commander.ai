"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface ChatModeContextType {
  isChatMode: boolean;
  enterChatMode: () => void;
  exitChatMode: () => void;
  chatThreadId: string | null;
}

const ChatModeContext = createContext<ChatModeContextType | undefined>(undefined);

export function ChatModeProvider({ children }: { children: ReactNode }) {
  const [isChatMode, setIsChatMode] = useState(false);
  const [chatThreadId, setChatThreadId] = useState<string | null>(null);

  const enterChatMode = () => {
    setIsChatMode(true);
    // Generate a thread ID for this chat session
    if (!chatThreadId) {
      setChatThreadId(crypto.randomUUID());
    }
  };

  const exitChatMode = () => {
    setIsChatMode(false);
  };

  return (
    <ChatModeContext.Provider value={{ isChatMode, enterChatMode, exitChatMode, chatThreadId }}>
      {children}
    </ChatModeContext.Provider>
  );
}

export function useChatMode() {
  const context = useContext(ChatModeContext);
  if (!context) {
    throw new Error("useChatMode must be used within ChatModeProvider");
  }
  return context;
}
