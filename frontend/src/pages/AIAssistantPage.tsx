// frontend/src/pages/AIAssistantPage.tsx
import React, { useState } from "react";
import { sendAssistantMessage, ChatMessagePayload } from "../services/assistant";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  source?: string;
  time: string;
}

const QUICK_QUESTIONS = [
  "Where am I spending the most?",
  "How much did I spend this month?",
  "Will I run out of money before month end?",
  "Which expenses can I reduce?",
  "What unusual transactions were detected?",
  "How much can I save next month?",
];

const AIAssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-msg",
      sender: "assistant",
      text: "Namaste! I am your FinPulse AI Daily Expense Coach. I have live access to your bank ledger in INR (₹), UPI payments, monthly bills, and anomaly alerts. How can I help you manage your expenses or savings today?",
      source: "AI (Gemini)",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (messageText?: string) => {
    const query = (messageText || input).trim();
    if (!query || loading) return;

    const userMsgId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
    const userMsg: Message = {
      id: userMsgId,
      sender: "user",
      text: query,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    // Build history for backend (last 6 messages)
    const historyPayload: ChatMessagePayload[] = messages
      .filter((m) => m.id !== "initial-msg")
      .slice(-6)
      .map((m) => ({
        role: m.sender === "user" ? "user" : "assistant",
        content: m.text,
      }));

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendAssistantMessage(query, historyPayload);
      const botMsgId = `bot-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
      const botMsg: Message = {
        id: botMsgId,
        sender: "assistant",
        text: res.response,
        source: res.source || "AI (Gemini)",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsgId = `err-${Date.now()}`;
      const errorMsg: Message = {
        id: errorMsgId,
        sender: "assistant",
        text:
          err.response?.data?.detail ||
          "I am temporarily unable to connect with the assistant. Please verify your connection or try again shortly.",
        source: "Offline mode",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 flex flex-col h-[calc(100vh-6.5rem)] pb-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <span>Daily Expense Coach</span>
            <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium">
              Gemini & INR (₹)
            </span>
          </h1>
          <p className="text-sm text-slate-500">
            Real-time conversational financial guidance grounded directly in your PostgreSQL ledger
          </p>
        </div>
      </div>

      {/* Quick Prompts Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <span className="text-xs font-semibold text-slate-400 whitespace-nowrap">Suggested:</span>
        {QUICK_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            disabled={loading}
            className="text-xs bg-white hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 text-slate-700 px-3 py-1.5 rounded-full whitespace-nowrap shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-2xl px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-xs ${
                m.sender === "user"
                  ? "bg-emerald-600 text-white rounded-br-none"
                  : "bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-none"
              }`}
            >
              <div className="whitespace-pre-wrap">{m.text}</div>
            </div>

            <div className="flex items-center gap-2 mt-1 px-1">
              {m.sender === "assistant" && m.source && (
                <span
                  className={`text-[10px] font-medium px-1.5 py-0.2 rounded ${
                    m.source.includes("AI")
                      ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                      : "bg-slate-200 text-slate-600 border border-slate-300"
                  }`}
                >
                  {m.source}
                </span>
              )}
              <span className="text-[10px] text-slate-400">{m.time}</span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs py-2 bg-slate-50 px-3 rounded-lg border border-slate-200 w-fit">
            <div className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce"></div>
            <div
              className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce"
              style={{ animationDelay: "0.2s" }}
            ></div>
            <div
              className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce"
              style={{ animationDelay: "0.4s" }}
            ></div>
            <span className="text-slate-600 font-medium">Analyzing verified Indian ledger...</span>
          </div>
        )}
      </div>

      {/* Message Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your UPI spending, bills, balance, or savings in ₹..."
          disabled={loading}
          className="flex-1 p-3 border border-slate-300 rounded-xl text-sm bg-white shadow-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default AIAssistantPage;
