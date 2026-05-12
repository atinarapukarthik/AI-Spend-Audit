import { Metadata } from "next";
import { createClient } from "@supabase/supabase-js";
import { notFound } from "next/navigation";
import MonitoringProtocol from "./monitoring-protocol";
import ReviewToast from "./review-toast";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;

  return {
    title: `Tactical Resource Memorandum — ${id.slice(0, 8)}`,
    description: `Strategic AI spend optimisation analysis and capital reallocation assessment`,
    openGraph: {
      title: `Tactical Resource Memorandum — AI Spend Audit`,
      description: `Classified strategic analysis of organisational AI tool capital expenditure and optimisation surface`,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: `Tactical Resource Memorandum — AI Spend Audit`,
      description: `Strategic analysis of AI tool expenditure with actionable recommendations`,
    },
  };
}

async function getAuditData(auditId: string) {
  const { data, error } = await supabase
    .from("audits")
    .select("savings_data, ai_summary, created_at")
    .eq("id", auditId)
    .single();

  if (error || !data) {
    return null;
  }

  return data;
}

export default async function AuditResultsPage({ params }: PageProps) {
  const { id } = await params;

  const auditData = await getAuditData(id);

  if (!auditData) {
    notFound();
  }

  const { savings_data, ai_summary, created_at } = auditData;
  const tools = savings_data?.tools || [];
  const totalMonthlySavings = savings_data?.total_monthly_savings || 0;
  const totalAnnualSavings = totalMonthlySavings * 12;

  const isHighValue = totalMonthlySavings > 500;

  const formattedDate = new Date(created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="min-h-screen bg-zinc-950 py-6 sm:py-12 px-3 sm:px-4">
      <ReviewToast />
      <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">

        {/* Header — Classified Document Masthead */}
        <div className="border border-zinc-800 rounded-xl sm:rounded-2xl bg-zinc-900/50 overflow-hidden">
          <div className="border-b border-zinc-800 px-4 sm:px-8 py-3 sm:py-5">
            <p className="text-[10px] sm:text-xs text-zinc-500 font-mono uppercase tracking-widest mb-1">
              CLASSIFIED // TACTICAL RESOURCE MEMORANDUM
            </p>
            <p className="text-[11px] sm:text-sm text-zinc-600 font-mono">
              Issued: {formattedDate} &nbsp;//&nbsp; Ref: {id.slice(0, 8)}
            </p>
          </div>

          {/* Hero Metric */}
          <div className="px-4 sm:px-8 py-6 sm:py-8 text-center border-b border-zinc-800">
            <p className="text-[10px] sm:text-xs text-zinc-500 font-mono uppercase tracking-wider mb-2 sm:mb-3">
              Total Capital Liquidity Recovery Identified
            </p>
            <div className="text-3xl sm:text-5xl font-bold text-zinc-100 font-mono tracking-tight">
              ${totalMonthlySavings.toLocaleString()}
              <span className="text-sm sm:text-lg text-zinc-500 ml-1 sm:ml-2">/mo</span>
            </div>
            <p className="text-sm sm:text-lg text-zinc-400 font-mono mt-1 sm:mt-2">
              ${totalAnnualSavings.toLocaleString()}/yr
            </p>
          </div>
        </div>

        {/* Tactical Resource Memorandum — AI Summary */}
        <div className="border border-zinc-800 rounded-xl sm:rounded-2xl bg-zinc-900/50 overflow-hidden">
          <div className="border-b border-zinc-800 px-4 sm:px-8 py-3 sm:py-4">
            <p className="text-[10px] sm:text-xs text-zinc-500 font-mono uppercase tracking-widest">
              MEMORANDUM BODY
            </p>
          </div>
          <div className="px-4 sm:px-8 py-4 sm:py-6">
            <div className="text-zinc-300 leading-relaxed font-mono text-xs sm:text-sm space-y-4 whitespace-pre-line">
              {ai_summary || "Analysis incomplete. Memorandum not yet generated."}
            </div>
          </div>
        </div>

        {/* Conditional Action — High Value Only */}
        {isHighValue && (
          <div className="border border-zinc-800 rounded-xl sm:rounded-2xl bg-zinc-900/50 px-4 sm:px-8 py-5 sm:py-6 text-center">
            <p className="text-[10px] sm:text-xs text-zinc-500 font-mono uppercase tracking-wider mb-2 sm:mb-3">
              Action Required — Capital Recovery Threshold Exceeded
            </p>
            <p className="text-xs sm:text-sm text-zinc-400 font-mono mb-4 sm:mb-5">
              Liquidity leakage of ${totalMonthlySavings.toLocaleString()}/mo detected.
              Schedule a strategic intervention to capture identified yield.
            </p>
            <a
              href="https://calendly.com/credex/ai-spend-audit"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block w-full sm:w-auto px-6 sm:px-8 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 font-mono text-xs sm:text-sm uppercase tracking-wider transition-colors"
            >
              Schedule Strategic Intervention
            </a>
          </div>
        )}

        {/* Protocol: Continuous Monitoring — Visible on ALL states */}
        <MonitoringProtocol auditId={id} />

        {/* Tool-by-Tool Breakdown */}
        <div className="border border-zinc-800 rounded-xl sm:rounded-2xl bg-zinc-900/50 overflow-hidden">
          <div className="border-b border-zinc-800 px-4 sm:px-8 py-3 sm:py-4">
            <p className="text-[10px] sm:text-xs text-zinc-500 font-mono uppercase tracking-widest">
              Asset Inventory — Variable Breakdown
            </p>
          </div>
          <div className="px-4 sm:px-8 py-4 sm:py-6">
            {tools.length === 0 ? (
              <p className="text-zinc-500 font-mono text-sm text-center py-4">
                No variables analysed.
              </p>
            ) : (
              <div className="space-y-2 sm:space-y-3">
                {tools.map((tool: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 sm:p-4 border border-zinc-800 bg-zinc-900/30 gap-2"
                  >
                    <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-shrink">
                      <div className="w-7 h-7 sm:w-9 sm:h-9 border border-zinc-700 flex items-center justify-center flex-shrink-0">
                        <span className="text-[10px] sm:text-sm font-mono font-bold text-zinc-400">
                          {tool.tool_name?.charAt(0) || "?"}
                        </span>
                      </div>
                      <div className="min-w-0">
                        <p className="font-mono text-xs sm:text-sm font-semibold text-zinc-200 truncate">
                          {tool.tool_name || tool.tool}
                        </p>
                        <p className="text-[10px] sm:text-xs font-mono text-zinc-500 truncate">
                          {tool.current_plan} → {tool.recommended_plan}
                        </p>
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0 ml-auto">
                      {tool.monthly_savings > 0 ? (
                        <>
                          <p className="text-xs sm:text-sm font-mono font-bold text-zinc-300">
                            -${tool.monthly_savings}/mo
                          </p>
                          <p className="text-[10px] sm:text-xs font-mono text-zinc-600">
                            ${tool.current_spend} → ${tool.recommended_spend}
                          </p>
                        </>
                      ) : (
                        <p className="text-[10px] sm:text-xs font-mono text-zinc-600">
                          Stable
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer — Classification Footer */}
        <div className="text-center border-t border-zinc-800 pt-4 sm:pt-6">
          <p className="text-[10px] sm:text-xs font-mono text-zinc-700">
            Credex Strategic Analysis Engine &nbsp;//&nbsp; {formattedDate}
          </p>
        </div>
      </div>
    </div>
  );
}
