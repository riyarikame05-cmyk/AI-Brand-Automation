"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

const EXTENSIONS_API = "http://127.0.0.1:8001";

interface LogoVariation {
  type: string;
  filename: string;
  url: string;
}

interface LogoVariationsResponse {
  project_id: string;
  business_name: string;
  master_logo: {
    id: string;
    url: string;
  };
  variations: LogoVariation[];
  count: number;
}

const VARIATION_INFO: Record<
  string,
  {
    name: string;
    description: string;
  }
> = {
  light: {
    name: "Light",
    description:
      "Primary identity prepared for bright and neutral surfaces.",
  },
  dark: {
    name: "Dark",
    description:
      "Brand presentation prepared for dark interfaces and backgrounds.",
  },
  monochrome: {
    name: "Monochrome",
    description:
      "Single-tone treatment for documents, printing and simplified applications.",
  },
  avatar: {
    name: "Icon / Avatar",
    description:
      "Square format prepared for profiles, app icons and social channels.",
  },
};

export default function BrandToolsPage() {
  const params = useParams<{ id: string }>();
  const projectId = params?.id;

  const [data, setData] =
    useState<LogoVariationsResponse | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function generateVariations() {
    if (!projectId || loading) return;

    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${EXTENSIONS_API}/projects/${projectId}/logo-variations`,
        {
          method: "POST",
          headers: {
            Accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        let message =
          "Could not generate logo variations.";

        try {
          const body = await response.json();

          if (body?.detail) {
            message = body.detail;
          }
        } catch {
          // Keep fallback message.
        }

        throw new Error(message);
      }

      const result: LogoVariationsResponse =
        await response.json();

      setData(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not generate logo variations."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f7f7fb] text-zinc-900">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
      >
        <div className="absolute -left-48 top-20 h-[600px] w-[600px] rounded-full bg-violet-300/20 blur-[150px]" />
        <div className="absolute -right-48 top-[500px] h-[600px] w-[600px] rounded-full bg-blue-200/20 blur-[150px]" />
      </div>

      <header className="relative z-10 border-b border-white/80 bg-white/75 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <Link
            href="/"
            className="flex items-center gap-2.5"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-950 text-sm font-bold text-white">
              B
            </div>

            <span className="text-[15px] font-semibold">
              BrandAI
            </span>
          </Link>

          <div className="flex items-center gap-2">
            <Link
              href={`/projects/${projectId}`}
              className="rounded-lg px-3 py-2 text-sm font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900"
            >
              ← Project
            </Link>

            <Link
              href="/dashboard"
              className="rounded-lg bg-zinc-950 px-3.5 py-2 text-sm font-semibold text-white"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-7xl px-6 py-12 lg:px-8">
        <div className="flex flex-col justify-between gap-7 border-b border-zinc-200 pb-9 lg:flex-row lg:items-end">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
                Brand Tools
              </span>

              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                Local
              </span>
            </div>

            <h1 className="mt-5 text-4xl font-semibold tracking-[-0.04em] text-zinc-950 sm:text-5xl">
              Logo variations
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-500 sm:text-base">
              Turn your selected master logo into practical
              identity formats for different surfaces and
              brand applications.
            </p>
          </div>

          <button
            type="button"
            onClick={generateVariations}
            disabled={loading}
            className="inline-flex h-11 items-center justify-center rounded-xl bg-zinc-950 px-5 text-sm font-semibold text-white shadow-lg transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? "Generating locally..."
              : data
                ? "↻ Regenerate variations"
                : "Generate variations"}
          </button>
        </div>

        {error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {!data && !loading && (
          <section className="mt-8 rounded-[26px] border border-dashed border-violet-200 bg-white/70 px-6 py-20 text-center shadow-sm">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100 text-2xl text-violet-700">
              ◇
            </div>

            <h2 className="mt-5 text-xl font-semibold text-zinc-950">
              Create your identity variations
            </h2>

            <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-zinc-500">
              Your selected master logo stays untouched.
              BrandAI creates four separate downloadable PNG
              derivatives locally.
            </p>

            <button
              type="button"
              onClick={generateVariations}
              className="mt-6 rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-violet-700"
            >
              Generate logo variations
            </button>
          </section>
        )}

        {loading && (
          <section className="mt-8 rounded-[26px] border border-violet-100 bg-white/85 px-6 py-20 text-center shadow-sm">
            <div className="mx-auto h-9 w-9 animate-spin rounded-full border-[3px] border-violet-100 border-t-violet-600" />

            <p className="mt-5 text-sm font-semibold text-zinc-800">
              Preparing your logo system...
            </p>

            <p className="mt-1 text-xs text-zinc-400">
              Everything is being processed locally.
            </p>
          </section>
        )}

        {data && !loading && (
          <>
            <section className="mt-8 flex flex-col justify-between gap-3 rounded-2xl border border-emerald-100 bg-emerald-50/70 px-5 py-4 sm:flex-row sm:items-center">
              <div>
                <p className="text-sm font-semibold text-emerald-900">
                  {data.business_name}
                </p>

                <p className="mt-0.5 text-xs text-emerald-700">
                  {data.count} logo variations generated from
                  your selected identity.
                </p>
              </div>

              <span className="text-xs font-semibold text-emerald-700">
                ✓ Master logo preserved
              </span>
            </section>

            <section className="mt-6 grid gap-5 md:grid-cols-2">
              {data.variations.map((variation) => {
                const info =
                  VARIATION_INFO[variation.type] ?? {
                    name: variation.type,
                    description:
                      "Generated brand identity variation.",
                  };

                const dark =
                  variation.type === "dark";

                return (
                  <article
                    key={variation.filename}
                    className="overflow-hidden rounded-[24px] border border-white/90 bg-white shadow-[0_15px_45px_rgba(24,24,27,0.06)]"
                  >
                    <div
                      className={`flex aspect-[4/3] items-center justify-center p-8 ${
                        dark
                          ? "bg-[#111114]"
                          : "bg-white"
                      }`}
                    >
                      <img
                        src={variation.url}
                        alt={`${data.business_name} ${info.name} logo`}
                        className="max-h-full max-w-full object-contain"
                      />
                    </div>

                    <div className="border-t border-zinc-100 p-5">
                      <div className="flex items-start justify-between gap-5">
                        <div>
                          <p className="text-sm font-semibold text-zinc-950">
                            {info.name}
                          </p>

                          <p className="mt-1 max-w-md text-xs leading-5 text-zinc-500">
                            {info.description}
                          </p>
                        </div>

                        <span className="rounded-full bg-violet-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-violet-700">
                          PNG
                        </span>
                      </div>

                      <a
                        href={variation.url}
                        download={variation.filename}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-5 flex h-10 w-full items-center justify-center rounded-xl bg-zinc-950 text-sm font-semibold text-white transition hover:bg-zinc-800"
                      >
                        ↓ Download {info.name}
                      </a>
                    </div>
                  </article>
                );
              })}
            </section>
          </>
        )}

        <section className="mt-10 border-t border-zinc-200 pt-8">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-400">
            Coming next
          </p>

          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {[
              "Brand Mockups",
              "Social Media Kit",
              "Video Studio",
            ].map((tool) => (
              <div
                key={tool}
                className="rounded-2xl border border-white bg-white/65 p-5 text-sm font-semibold text-zinc-500"
              >
                {tool}
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}