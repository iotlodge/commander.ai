"use client";

import { useState, useRef, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { X, Copy, Check, Send, Loader2, MessageSquare, Maximize2, Minimize2 } from 'lucide-react';
import { MarkdownRenderer } from '@/components/ui/markdown-renderer';
import { AgentTask, TaskStatus } from '@/lib/types';
import { useTaskStore } from '@/lib/store';

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChatModal({ isOpen, onClose }: ChatModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [sessionTaskId, setSessionTaskId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [metrics, setMetrics] = useState({ llmCalls: 0, tokens: 0 });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Create session task when modal opens, complete it when closing
  useEffect(() => {
    const createSessionTask = async () => {
      try {
        // Create the session task
        const response = await fetch("http://localhost:8000/api/commands?user_id=00000000-0000-0000-0000-000000000001", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: "00000000-0000-0000-0000-000000000001",
            text: "@chat [Chat Session Started]",
          }),
        });

        if (response.ok) {
          const task = await response.json();
          setSessionTaskId(task.id);

          // Immediately update to IN_PROGRESS to prevent automatic execution
          // and set initial result
          await fetch(`http://localhost:8000/api/tasks/${task.id}?user_id=00000000-0000-0000-0000-000000000001`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              status: "in_progress",
              result: "# Chat Session (Active)\n\nWaiting for messages...",
            }),
          });
        }
      } catch (error) {
        console.error("Failed to create session task:", error);
      }
    };

    const completeSessionTask = async () => {
      if (!sessionTaskId) return;

      try {
        // Format the conversation as markdown
        const conversationMarkdown = messages.map(m =>
          `**${m.role === 'user' ? 'You' : 'Assistant'}**: ${m.content}`
        ).join('\n\n');

        const fullResult = messages.length > 0
          ? `# Chat Session Summary\n\n**Messages Exchanged**: ${messages.length}\n**LLM Calls**: ${metrics.llmCalls}\n**Total Tokens**: ${metrics.tokens.toLocaleString()}\n\n---\n\n${conversationMarkdown}`
          : `# Chat Session Summary\n\n**No messages exchanged**`;

        // Update the task to completed status using PATCH
        await fetch(`http://localhost:8000/api/tasks/${sessionTaskId}?user_id=00000000-0000-0000-0000-000000000001`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            status: "completed",
            result: fullResult,
          }),
        });
      } catch (error) {
        console.error("Failed to complete session task:", error);
      }
    };

    if (isOpen && !sessionTaskId) {
      // Modal just opened, create session task
      createSessionTask();
    } else if (!isOpen && sessionTaskId) {
      // Modal is closing, complete the session task
      completeSessionTask();
      setSessionTaskId(null);
    }

    return () => {
      // Cleanup on unmount
      if (sessionTaskId && !isOpen) {
        completeSessionTask();
      }
    };
  }, [isOpen, sessionTaskId, messages, metrics]);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Helper function to update session task with latest conversation
  const updateSessionTask = async (updatedMessages: ChatMessage[], currentMetrics: { llmCalls: number; tokens: number }) => {
    if (!sessionTaskId) return;

    try {
      const conversationMarkdown = updatedMessages.map(m =>
        `**${m.role === 'user' ? 'You' : 'Assistant'}**: ${m.content}`
      ).join('\n\n');

      const fullResult = `# Chat Session (In Progress)\n\n**Messages**: ${updatedMessages.length}\n**LLM Calls**: ${currentMetrics.llmCalls}\n**Tokens**: ${currentMetrics.tokens.toLocaleString()}\n\n---\n\n${conversationMarkdown}`;

      // Update task result while keeping it in progress (don't change status)
      await fetch(`http://localhost:8000/api/tasks/${sessionTaskId}?user_id=00000000-0000-0000-0000-000000000001`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          result: fullResult,
        }),
      });
    } catch (error) {
      console.error("Failed to update session task:", error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isSubmitting) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    // Add user message immediately
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputValue("");
    setIsSubmitting(true);

    try {
      // Call the direct chat endpoint (doesn't create a task)
      const response = await fetch("http://localhost:8000/api/chat/message?user_id=00000000-0000-0000-0000-000000000001", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: "00000000-0000-0000-0000-000000000001",
          message: userMessage.content,
          thread_id: threadId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status}`);
      }

      const chatResponse = await response.json();

      // Store thread_id for subsequent messages
      if (!threadId) {
        setThreadId(chatResponse.thread_id);
      }

      // Add assistant response
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: chatResponse.response,
        timestamp: new Date(),
      };

      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);

      // Update metrics
      const updatedMetrics = {
        llmCalls: metrics.llmCalls + (chatResponse.metrics.llm_calls || 0),
        tokens: metrics.tokens + (chatResponse.metrics.tokens.total || 0),
      };
      setMetrics(updatedMetrics);

      // Update session task with latest conversation
      await updateSessionTask(finalMessages, updatedMetrics);

      setIsSubmitting(false);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: "⚠️ Failed to send message. Please try again.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsSubmitting(false);
    }
  };

  const handleCopyChat = async () => {
    const formatted = messages.map(m =>
      `**${m.role === 'user' ? 'You' : 'Assistant'}**: ${m.content}\n\n`
    ).join('');

    const fullText = `# Chat with LLM\n\n${formatted}`;

    try {
      await navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleExitChat = () => {
    // Let the useEffect handle completing the session task
    setMessages([]);
    setThreadId(null);
    setInputValue("");
    setMetrics({ llmCalls: 0, tokens: 0 });
    setIsSubmitting(false);
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleExitChat()}>
      <DialogContent className={`${isMaximized ? 'w-[95vw] max-w-[95vw] max-h-[92vh] sm:max-w-[95vw]' : 'w-full max-w-4xl max-h-[85vh] sm:max-w-4xl'} bg-[#1e2433] border-gray-700 overflow-hidden flex flex-col transition-all duration-200`}>
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-2xl font-bold text-white flex items-center justify-between">
            <div className="flex items-center gap-3">
              <MessageSquare className="h-6 w-6 text-[#4a9eff]" />
              <span>Chat with LLM</span>
            </div>
            <div className="flex items-center gap-4">
              {/* Metrics Display */}
              <div className="flex gap-4 text-sm">
                <div className="text-[#4a9eff]">
                  LLM Calls: {metrics.llmCalls}
                </div>
                <div className="text-purple-400">
                  Total Tokens: {metrics.tokens.toLocaleString()}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                {messages.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyChat}
                    className="gap-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border-blue-500/30"
                  >
                    {copied ? (
                      <>
                        <Check className="h-4 w-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Copy Chat
                      </>
                    )}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMaximized(!isMaximized)}
                  className="hover:bg-gray-700/50"
                  title={isMaximized ? "Restore size" : "Maximize"}
                >
                  {isMaximized ? (
                    <Minimize2 className="h-5 w-5" />
                  ) : (
                    <Maximize2 className="h-5 w-5" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleExitChat}
                  className="hover:bg-gray-700/50"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </DialogTitle>
        </DialogHeader>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2 py-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <MessageSquare className="h-16 w-16 text-gray-600 mb-4" />
              <p className="text-gray-400 text-lg">Start a conversation</p>
              <p className="text-sm text-gray-500 mt-2">
                Type a message below to chat with the AI assistant
              </p>
            </div>
          ) : (
            <>
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg p-4 ${
                      message.role === 'user'
                        ? 'bg-blue-500/20 border border-blue-500/30 text-white ml-auto'
                        : 'bg-[#2a3444] border border-[#3a4454] text-gray-200 mr-auto'
                    }`}
                  >
                    <div className="text-xs text-gray-400 mb-1">
                      {message.role === 'user' ? 'You' : 'Assistant'}
                    </div>
                    {message.role === 'assistant' ? (
                      <MarkdownRenderer
                        content={message.content}
                        variant="default"
                        className="text-sm"
                      />
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>
                </div>
              ))}

              {/* Loading indicator */}
              {isSubmitting && (
                <div className="flex justify-start">
                  <div className="max-w-[70%] rounded-lg p-4 bg-[#2a3444] border border-[#3a4454] text-gray-200 mr-auto">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="flex-shrink-0 border-t border-[#3a4454] pt-4">
          <div className="flex gap-2">
            <Textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
              className="flex-1 min-h-[60px] max-h-[200px] bg-[#1a1f2e] border-[#3a4454] text-white resize-none"
              disabled={isSubmitting}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isSubmitting}
              className="bg-[#4a9eff] hover:bg-[#3a8eef] text-white"
            >
              {isSubmitting ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
