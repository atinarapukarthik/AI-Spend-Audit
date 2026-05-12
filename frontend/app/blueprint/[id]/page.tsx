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
    title: `Tactical Resource Memorandum`,
    description: `Strategic AI spend optimisation analysis`,
  };
}

async function getBlueprint(blueprintId: string) {
  const { data, error } = await supabase
    .from("blueprints")
    .select("content, created_at")
    .eq("id", blueprintId)
    .single();

  if (error || !data) return null;
  return data;
}

export default async function BlueprintPage({ params }: PageProps) {
  const { id } = await params;
  const blueprint = await getBlueprint(id);

  if (!blueprint) {
    notFound();
  }

  const formattedDate = new Date(blueprint.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="min-h-screen bg-zinc-950 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="border border-zinc-800 rounded-2xl bg-zinc-900/50 overflow-hidden">
          <div className="border-b border-zinc-800 px-8 py-6">
            <p className="text-xs text-zinc-500 font-mono uppercase tracking-wider mb-1">
              CLASSIFIED // TACTICAL
            </p>
            <h1 className="text-2xl font-bold text-zinc-100">
              Tactical Resource Memorandum
            </h1>
            <p className="text-sm text-zinc-500 mt-1">
              Issued {formattedDate}
            </p>
          </div>
          <div className="px-8 py-8">
            <div className="prose prose-invert prose-zinc max-w-none">
              {blueprint.content.split("\n").map((line: string, i: number) => {
                const trimmed = line.trim();
                if (!trimmed) return <br key={i} />;
                if (trimmed.match(/^#{1,3}\s/)) {
                  const level = trimmed.match(/^#+/)?.[0].length || 1;
                  const text = trimmed.replace(/^#+\s*/, "");
                  const Tag = `h${Math.min(level + 1, 4)}` as keyof JSX.IntrinsicElements;
                  return (
                    <Tag key={i} className="text-zinc-200 font-bold mt-6 mb-2 text-lg">
                      {text}
                    </Tag>
                  );
                }
                if (trimmed.match(/^[-*]\s/)) {
                  return (
                    <li key={i} className="text-zinc-300 ml-4 mb-1 list-disc">
                      {trimmed.replace(/^[-*]\s*/, "")}
                    </li>
                  );
                }
                return (
                  <p key={i} className="text-zinc-300 mb-3 leading-relaxed">
                    {trimmed}
                  </p>
                );
              })}
            </div>
          </div>
          <div className="border-t border-zinc-800 px-8 py-4">
            <p className="text-xs text-zinc-600 font-mono">
              Credex Strategic Analysis Engine // {formattedDate}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
