import { Metadata } from "next";
import { createClient } from "@supabase/supabase-js";
import { notFound } from "next/navigation";

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
    title: `Audit Results - ${id.slice(0, 8)}...`,
    description: `AI spending audit results and savings recommendations for your team`,
    openGraph: {
      title: `AI Spend Audit Results`,
      description: `Discover your potential savings on AI tool subscriptions`,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: `AI Spend Audit Results`,
      description: `View your personalized AI tool spending analysis and savings recommendations`,
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
  const isOptimized = totalMonthlySavings < 100;

  const formattedDate = new Date(created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-zinc-900 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50 mb-2">
            Your AI Spend Audit Results
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Generated on {formattedDate}
          </p>
        </div>

        {/* Hero Metric Card */}
        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-xl p-8 border border-zinc-200 dark:border-zinc-800">
          <div className="text-center">
            <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider mb-2">
              Total Potential Savings
            </p>
            <div className="flex items-center justify-center gap-2 mb-4">
              <span className="text-5xl font-bold text-green-600 dark:text-green-400">
                ${totalMonthlySavings.toLocaleString()}
              </span>
              <span className="text-xl text-zinc-500 dark:text-zinc-400">/mo</span>
            </div>
            <p className="text-2xl font-semibold text-zinc-700 dark:text-zinc-300">
              ${totalAnnualSavings.toLocaleString()}/year
            </p>
          </div>
        </div>

        {/* AI Summary Card */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 rounded-2xl p-6 border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/50 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                AI Analysis
              </h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Personalized recommendations for your team
              </p>
            </div>
          </div>
          <p className="text-zinc-700 dark:text-zinc-300 leading-relaxed">
            {ai_summary || "Your audit is being processed. Results will be available shortly."}
          </p>
        </div>

        {/* Conditional CTA */}
        {isHighValue ? (
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 rounded-2xl p-8 border border-amber-200 dark:border-amber-800 text-center">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 mb-2">
              Save ${totalMonthlySavings.toLocaleString()}/month Starting Today
            </h2>
            <p className="text-zinc-600 dark:text-zinc-400 mb-6">
              Book a free Credex consultation to implement these optimizations with zero risk.
            </p>
            <a
              href="https://calendly.com/credex/ai-spend-audit"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Book Credex Consultation
            </a>
            <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-4">
              Free 30-min optimization session • No commitment required
            </p>
          </div>
        ) : isOptimized ? (
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/30 rounded-2xl p-8 border border-emerald-200 dark:border-emerald-800 text-center">
            <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/50 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 mb-2">
              Your Stack is Highly Optimized
            </h2>
            <p className="text-zinc-600 dark:text-zinc-400">
              Great job! Your current AI tool configuration is already cost-effective. 
              Consider exploring advanced features or enterprise upgrades to unlock more value.
            </p>
          </div>
        ) : (
          <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 border border-zinc-200 dark:border-zinc-800 text-center">
            <p className="text-zinc-600 dark:text-zinc-400">
              You can save ${totalMonthlySavings}/month with minor plan adjustments. 
              Review the breakdown below for specific recommendations.
            </p>
          </div>
        )}

        {/* Tool Breakdown */}
        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-xl p-8 border border-zinc-200 dark:border-zinc-800">
          <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-50 mb-6">
            Tool-by-Tool Breakdown
          </h3>
          
          {tools.length === 0 ? (
            <p className="text-zinc-500 dark:text-zinc-400 text-center py-8">
              No tools analyzed yet.
            </p>
          ) : (
            <div className="space-y-4">
              {tools.map((tool: any, index: number) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-700"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-zinc-200 dark:bg-zinc-700 rounded-lg flex items-center justify-center">
                      <span className="text-lg font-bold text-zinc-600 dark:text-zinc-300">
                        {tool.tool_name?.charAt(0) || "?"}
                      </span>
                    </div>
                    <div>
                      <p className="font-semibold text-zinc-900 dark:text-zinc-50">
                        {tool.tool_name || tool.tool}
                      </p>
                      <p className="text-sm text-zinc-500 dark:text-zinc-400">
                        {tool.current_plan} → {tool.recommended_plan}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    {tool.monthly_savings > 0 ? (
                      <>
                        <p className="text-lg font-bold text-green-600 dark:text-green-400">
                          -${tool.monthly_savings}/mo
                        </p>
                        <p className="text-xs text-zinc-500 dark:text-zinc-400">
                          ${tool.current_spend} → ${tool.recommended_spend}
                        </p>
                      </>
                    ) : (
                      <p className="text-sm text-zinc-500 dark:text-zinc-400">
                        Already optimized
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-zinc-500 dark:text-zinc-400">
          <p>
            Powered by{" "}
            <span className="font-semibold text-zinc-700 dark:text-zinc-300">
              Credex AI
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}