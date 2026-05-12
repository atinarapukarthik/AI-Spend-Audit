"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface ToolInput {
  tool: string;
  plan: string;
  seats: number;
}

const AI_TOOLS = [
  { id: "cursor", name: "Cursor" },
  { id: "github_copilot", name: "GitHub Copilot" },
  { id: "claude", name: "Claude" },
  { id: "chatgpt", name: "ChatGPT" },
  { id: "gemini", name: "Gemini" },
  { id: "perplexity", name: "Perplexity Pro" },
  { id: "notion_ai", name: "Notion AI" },
  { id: "midjourney", name: "Midjourney" },
];

const PLANS = [
  { id: "hobby", name: "Hobby (Free)" },
  { id: "pro", name: "Pro" },
  { id: "team", name: "Team" },
  { id: "business", name: "Business" },
  { id: "enterprise", name: "Enterprise" },
];

export default function Home() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [tools, setTools] = useState<ToolInput[]>([
    { tool: "cursor", plan: "pro", seats: 1 },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const addTool = () => {
    setTools([...tools, { tool: "cursor", plan: "pro", seats: 1 }]);
  };

  const removeTool = (index: number) => {
    if (tools.length > 1) {
      setTools(tools.filter((_, i) => i !== index));
    }
  };

  const updateTool = (index: number, field: keyof ToolInput, value: string | number) => {
    const updated = [...tools];
    updated[index] = { ...updated[index], [field]: value };
    setTools(updated);
  };

  const [progressStep, setProgressStep] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("handleSubmit called!");
    console.log("Email:", email);
    console.log("Company:", companyName);
    console.log("Tools:", tools);
    setIsLoading(true);
    setError("");
    setProgressStep("Submitting your request...");

    try {
      setProgressStep("Calculating savings...");
      
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/generate-audit`;
      console.log("Calling API:", apiUrl);
      
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          company_name: companyName || null,
          tools,
        }),
      });

      console.log("Response status:", response.status);
      const data = await response.json();
      console.log("Response data:", data);

      if (!response.ok) {
        setError(data.detail || `Server error (${response.status}). Please try again.`);
        setProgressStep("");
        return;
      }

      if (data.status === "success" && data.audit_id) {
        setProgressStep("Redirecting to your results...");
        router.push(`/audit/${data.audit_id}`);
      } else {
        setError("Failed to generate audit. Please try again.");
      }
    } catch (err) {
      const errMessage = err instanceof Error ? err.message : "Unknown error";
      if (errMessage.includes("fetch")) {
        setError("Cannot connect to backend. Make sure the backend is running on port 8000.");
      } else {
        setError(`Error: ${errMessage}`);
      }
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-zinc-900 py-6 sm:py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-6 sm:mb-10">
          <h1 className="text-2xl sm:text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-2 sm:mb-3">
            AI Spend Audit
          </h1>
          <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400">
            Discover how much your team can save by optimizing AI tool subscriptions
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-zinc-900 rounded-xl sm:rounded-2xl shadow-xl p-4 sm:p-8 space-y-5 sm:space-y-8">
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              Contact Information
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Email *
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="you@company.com"
                />
              </div>
              <div>
                <label htmlFor="company" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Company Name
                </label>
                <input
                  id="company"
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Acme Corp"
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base sm:text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                AI Tools
              </h2>
              <button
                type="button"
                onClick={addTool}
                className="text-xs sm:text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 whitespace-nowrap"
              >
                + Add another tool
              </button>
            </div>

            <div className="space-y-4">
              {tools.map((tool, index) => (
                <div
                  key={index}
                  className="p-4 bg-zinc-50 dark:bg-zinc-800 rounded-lg space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                      Tool {index + 1}
                    </span>
                    {tools.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeTool(index)}
                        className="text-sm text-red-600 hover:text-red-700"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div>
                      <label className="block text-xs text-zinc-600 dark:text-zinc-400 mb-1">
                        Tool
                      </label>
                      <select
                        value={tool.tool}
                        onChange={(e) => updateTool(index, "tool", e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 text-sm"
                      >
                        {AI_TOOLS.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-zinc-600 dark:text-zinc-400 mb-1">
                        Current Plan
                      </label>
                      <select
                        value={tool.plan}
                        onChange={(e) => updateTool(index, "plan", e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 text-sm"
                      >
                        {PLANS.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-zinc-600 dark:text-zinc-400 mb-1">
                        Seats
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={tool.seats}
                        onChange={(e) => updateTool(index, "seats", parseInt(e.target.value) || 1)}
                        className="w-full px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 text-sm"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-500 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-3"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <div className="text-left">
                  <div>Analyzing your AI spend...</div>
                  <div className="text-xs text-blue-200 font-normal">{progressStep}</div>
                </div>
              </>
            ) : (
              "Generate My Savings Report"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
