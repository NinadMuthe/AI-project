// frontend/src/pages/AIAssistantPage.tsx
import React, { useState } from "react";
import { sendAssistantMessage } from "../services/assistant";

interface Message {
  sender: "user" | "assistant";
  text: string;
  time: string;
}

const QUICK_QUESTIONS = [
  "Where am I spending the most?",
  "How much did I spend this month?",
  "Will I run out of money before month end?",
  "Which expenses can I reduce?",
  "What unusual transactions were detected?",
];

const AIAssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "assistant",
      text: "Hello! I am your FinPulse AI Financial Advisor. I have direct access to your verified ledger balance, recent spending categories, forecast models, and anomaly alerts. How can I assist your financial planning today?",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (messageText?: string) => {
    const query = (messageText || input).trim();
    if (!query || loading) return;

    const userMsg: Message = {
      sender: "user",
      text: query,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendAssistantMessage(query);
      const botMsg: Message = {
        sender: "assistant",
        text: res.response,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        sender: "assistant",
        text:
          err.response?.data?.detail ||
          "I am temporarily unable to connect with the AI service. Please verify your connection or try again shortly.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <span>AI Financial Advisor</span>
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
              Gemini & LangChain
            </span>
          </h1>
          <p className="text-sm text-slate-500">
            Personalized, context-aware financial advice grounded in your actual transactions
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
            className="text-xs bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 text-slate-700 px-3 py-1.5 rounded-full whitespace-nowrap shadow-xs transition-colors disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 bg-white rounded-lg border border-slate-200 shadow-sm p-4 overflow-y-auto space-y-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-2xl px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                m.sender === "user"
                  ? "bg-indigo-600 text-white rounded-br-none shadow-xs"
                  : "bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-none"
              }`}
            >
              <div className="whitespace-pre-wrap">{m.text}</div>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 px-1">{m.time}</span>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs py-2">
            <div className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce"></div>
            <div
              className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce"
              style={{ animationDelay: "0.2s" }}
            ></div>
            <div
              className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce"
              style={{ animationDelay: "0.4s" }}
            ></div>
            <span>Analyzing financial context...</span>
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
          placeholder="Ask a question about your spending, budget, or balance..."
          disabled={loading}
          className="flex-1 p-3 border border-slate-300 rounded-lg text-sm bg-white shadow-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-5 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-xs transition-colors disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default AIAssistantPage;
