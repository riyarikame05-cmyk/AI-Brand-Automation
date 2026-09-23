"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

const API =
  process.env.NEXT_PUBLIC_API_URL?.replace(
    /\/$/,
    ""
  ) || "http://127.0.0.1:8000";

interface BrandScoreValues {
  memorability: number;
  simplicity: number;
  industry_fit: number;
  visual_consistency: number;
  color_effectiveness: number;
  audience_fit: number;
}

interface BrandScore {
  overall_score: number;
  scores: BrandScoreValues;
  strengths: string[];
  recommendations: string[];
  summary: string;
  ai_used: boolean;
  evaluation_mode: string;
}

interface BrandScoreResponse {
  project_id: string;
  business_name: string;
  brand_score: BrandScore;
}

interface BrandScorePanelProps {
  projectId: string;
}

export default function BrandScorePanel({
  projectId,
}: BrandScorePanelProps) {
  const [score, setScore] =
    useState<BrandScore | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadScore = useCallback(
    async () => {
      if (!projectId) return;

      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${API}/projects/${projectId}/brand-score`,
          {
            cache: "no-store",
          }
        );

        if (response.status === 400) {
          setScore(null);
          return;
        }

        if (!response.ok) {
          let message =
            "Could not evaluate brand.";

          try {
            const data =
              await response.json();

            message =
              data?.detail ||
              data?.message ||
              message;
          } catch {
            // Keep fallback message.
          }

          throw new Error(message);
        }

        const data: BrandScoreResponse =
          await response.json();

        setScore(data.brand_score);
      } catch (err) {
        console.error(
          "Brand score error:",
          err
        );

        setError(
          err instanceof Error
            ? err.message
            : "Could not evaluate brand."
        );
      } finally {
        setLoading(false);
      }
    },
    [projectId]
  );

  useEffect(() => {
    void loadScore();
  }, [loadScore]);

  return (
    <div className="mt-10">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">
              AI brand intelligence
            </p>

            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold text-emerald-700">
              Local AI
            </span>
          </div>

          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-950">
            Brand strength
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            A local AI evaluation of your
            selected identity, strategy,
            audience fit and visual system.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadScore()}
          disabled={loading}
          className="inline-flex h-10 shrink-0 items-center justify-center rounded-xl border border-zinc-200 bg-white px-4 text-xs font-semibold text-zinc-700 shadow-sm transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading
            ? "Evaluating..."
            : "Re-evaluate"}
        </button>
      </div>

      {loading && !score && (
        <div className="mt-5 flex min-h-[220px] items-center justify-center rounded-[24px] border border-violet-100 bg-white/90 shadow-sm">
          <div className="text-center">
            <div className="studio-spinner mx-auto h-8 w-8 rounded-full border-[3px] border-violet-100 border-t-violet-600" />

            <p className="mt-4 text-sm font-semibold text-zinc-800">
              Evaluating your brand...
            </p>

            <p className="mt-1 text-xs text-zinc-400">
              Ollama is reviewing the
              selected identity locally.
            </p>
          </div>
        </div>
      )}

      {error && !score && (
        <div className="mt-5 rounded-[20px] border border-amber-200 bg-amber-50 p-5">
          <p className="text-sm font-semibold text-amber-800">
            Brand evaluation unavailable
          </p>

          <p className="mt-1 text-xs leading-5 text-amber-700">
            {error}
          </p>

          <button
            type="button"
            onClick={() =>
              void loadScore()
            }
            className="mt-4 rounded-lg bg-amber-100 px-3 py-2 text-xs font-semibold text-amber-900"
          >
            Try again
          </button>
        </div>
      )}

      {score && (
        <div className="mt-5 overflow-hidden rounded-[26px] border border-white/90 bg-white/95 shadow-[0_18px_55px_rgba(24,24,27,0.07)]">
          <div className="grid lg:grid-cols-[0.72fr_1.28fr]">
            <div className="relative overflow-hidden bg-zinc-950 p-8 text-white sm:p-10">
              <div className="absolute -right-20 -top-20 h-56 w-56 rounded-full bg-violet-600/30 blur-[70px]" />

              <div className="relative">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-300">
                  Overall strength
                </p>

                <div className="mt-6 flex items-end gap-2">
                  <span className="text-7xl font-semibold tracking-[-0.07em]">
                    {score.overall_score}
                  </span>

                  <span className="pb-2 text-lg text-zinc-400">
                    /100
                  </span>
                </div>

                <p className="mt-5 text-sm font-semibold">
                  {getRating(
                    score.overall_score
                  )}
                </p>

                <p className="mt-3 text-xs leading-5 text-zinc-400">
                  {score.evaluation_mode}
                </p>

                <span className="mt-6 inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] font-semibold text-zinc-300">
                  {score.ai_used
                    ? "Ollama analysis active"
                    : "Deterministic analysis"}
                </span>
              </div>
            </div>

            <div className="p-7 sm:p-9">
              <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
                <ScoreBar
                  label="Memorability"
                  value={
                    score.scores
                      .memorability
                  }
                />

                <ScoreBar
                  label="Simplicity"
                  value={
                    score.scores
                      .simplicity
                  }
                />

                <ScoreBar
                  label="Industry fit"
                  value={
                    score.scores
                      .industry_fit
                  }
                />

                <ScoreBar
                  label="Visual consistency"
                  value={
                    score.scores
                      .visual_consistency
                  }
                />

                <ScoreBar
                  label="Color effectiveness"
                  value={
                    score.scores
                      .color_effectiveness
                  }
                />

                <ScoreBar
                  label="Audience fit"
                  value={
                    score.scores
                      .audience_fit
                  }
                />
              </div>

              <div className="mt-8 border-t border-zinc-100 pt-6">
                <p className="text-sm leading-7 text-zinc-600">
                  {score.summary}
                </p>
              </div>
            </div>
          </div>

          <div className="grid border-t border-zinc-100 lg:grid-cols-2">
            <div className="p-7 sm:p-8 lg:border-r lg:border-zinc-100">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-600">
                Key strengths
              </p>

              <div className="mt-4 space-y-3">
                {score.strengths.map(
                  (item, index) => (
                    <InsightRow
                      key={`${item}-${index}`}
                      marker="✓"
                      text={item}
                      variant="strength"
                    />
                  )
                )}
              </div>
            </div>

            <div className="p-7 sm:p-8">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-violet-600">
                AI recommendations
              </p>

              <div className="mt-4 space-y-3">
                {score.recommendations.map(
                  (item, index) => (
                    <InsightRow
                      key={`${item}-${index}`}
                      marker={String(
                        index + 1
                      )}
                      text={item}
                      variant="recommendation"
                    />
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getRating(
  score: number
) {
  if (score >= 90) {
    return "Excellent brand foundation";
  }

  if (score >= 80) {
    return "Strong brand foundation";
  }

  if (score >= 70) {
    return "Promising brand foundation";
  }

  return "Developing brand foundation";
}

function ScoreBar({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const normalized =
    Math.max(
      0,
      Math.min(
        100,
        Number(value) || 0
      )
    );

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <p className="text-xs font-medium text-zinc-600">
          {label}
        </p>

        <p className="text-xs font-semibold text-zinc-900">
          {normalized}
        </p>
      </div>

      <div className="mt-2 h-2 overflow-hidden rounded-full bg-zinc-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-violet-600 via-violet-500 to-blue-500 transition-all duration-700"
          style={{
            width: `${normalized}%`,
          }}
        />
      </div>
    </div>
  );
}

function InsightRow({
  marker,
  text,
  variant,
}: {
  marker: string;
  text: string;
  variant:
    | "strength"
    | "recommendation";
}) {
  const strength =
    variant === "strength";

  return (
    <div className="flex gap-3">
      <span
        className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
          strength
            ? "bg-emerald-50 text-emerald-600"
            : "bg-violet-50 text-violet-600"
        }`}
      >
        {marker}
      </span>

      <p className="text-sm leading-6 text-zinc-600">
        {text}
      </p>
    </div>
  );
}