"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  data?: ChatResponse;
}

const EXAMPLE_QUESTIONS = [
  "Which portfolios have the highest ESG risk?",
  "What are the top 10 most held assets across all portfolios?",
  "Show me portfolios that track MSCI Europe",
  "Which sectors have the most cross-portfolio exposure?",
  "What is the overlap between the EURO STOXX 50 and MSCI Europe portfolios?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || loading) return;

    const userMsg: Message = { role: "user", content: question.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setTimeout(scrollToBottom, 50);

    try {
      const response = await api.chat(question.trim());
      const assistantMsg: Message = {
        role: "assistant",
        content: response.answer,
        data: response,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: Message = {
        role: "assistant",
        content: `Failed to get a response. ${err instanceof Error ? err.message : "Please try again."}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    }

    setLoading(false);
    setTimeout(scrollToBottom, 50);
  }, [loading]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold tracking-tight">AI Chat</h1>
        <p className="text-sm text-slate-500 mt-1">
          Ask questions about portfolios, assets, and ESG data in natural language
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="text-4xl mb-4 opacity-20">💬</div>
              <h2 className="text-lg text-slate-400 mb-2">Ask anything about your graph</h2>
              <p className="text-sm text-slate-600 mb-6">
                Your question is translated to Cypher, executed against Neo4j, and the results are formatted into a clear answer.
              </p>
              <div className="space-y-2">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="block w-full text-left text-sm px-4 py-2.5 rounded-lg border border-slate-800 bg-[#0d1321] text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] ${msg.role === "user" ? "order-2" : ""}`}>
                {/* Message Bubble */}
                <div className={`rounded-xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-sky-600 text-white"
                    : "bg-[#0d1321] border border-slate-800 text-slate-200"
                }`}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>

                {/* Cypher Block (for assistant messages) */}
                {msg.data && (
                  <CypherBlock cypher={msg.data.cypher_query} confidence={msg.data.confidence} resultCount={msg.data.raw_results.length} />
                )}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#0d1321] border border-slate-800 rounded-xl px-4 py-3">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-800 pt-4">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about the knowledge graph..."
            rows={1}
            className="flex-1 px-4 py-3 rounded-xl border border-slate-800 bg-[#0d1321] text-sm text-slate-200 placeholder:text-slate-600 resize-none focus:outline-none focus:border-sky-700 transition-colors"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="px-5 py-3 rounded-xl bg-sky-600 text-white text-sm font-medium hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
        <p className="text-[10px] text-slate-600 mt-2 text-center">
          Powered by Claude — queries are validated to be read-only before execution
        </p>
      </div>
    </div>
  );
}

function CypherBlock({ cypher, confidence, resultCount }: { cypher: string; confidence: number; resultCount: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-2 rounded-lg border border-slate-800 bg-[#080c14] overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs text-slate-500 hover:text-slate-400 transition-colors"
      >
        <span className="font-mono">Cypher Query</span>
        <div className="flex items-center gap-3">
          <span className={`${confidence >= 0.7 ? "text-emerald-500" : confidence >= 0.4 ? "text-amber-500" : "text-red-500"}`}>
            {(confidence * 100).toFixed(0)}% confidence
          </span>
          <span>{resultCount} results</span>
          <span>{expanded ? "▲" : "▼"}</span>
        </div>
      </button>
      {expanded && (
        <div className="px-3 pb-3">
          <pre className="text-xs font-mono text-sky-300 whitespace-pre-wrap bg-[#060a12] rounded p-3 overflow-x-auto">
            {cypher}
          </pre>
        </div>
      )}
    </div>
  );
}
