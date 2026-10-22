"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const API =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

type Project = {
  id: string;
  business_name: string;
  description: string;
  industry: string;
  style: string;
  created_at: string;
};

function formatLabel(value: string) {
  if (!value) return "";

  return value
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Recently";
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

const CARD_THEMES = [
  {
    gradient: "from-violet-50 via-white to-indigo-50",
    glow: "bg-violet-300",
    mark: "text-violet-700",
    markBg: "bg-violet-50",
    colors: ["#18181b", "#7c3aed", "#ddd6fe"],
  },
  {
    gradient: "from-blue-50 via-white to-cyan-50",
    glow: "bg-blue-300",
    mark: "text-blue-700",
    markBg: "bg-blue-50",
    colors: ["#172554", "#2563eb", "#bfdbfe"],
  },
  {
    gradient: "from-amber-50 via-white to-orange-50",
    glow: "bg-amber-300",
    mark: "text-amber-700",
    markBg: "bg-amber-50",
    colors: ["#451a03", "#d97706", "#fde68a"],
  },
  {
    gradient: "from-emerald-50 via-white to-teal-50",
    glow: "bg-emerald-300",
    mark: "text-emerald-700",
    markBg: "bg-emerald-50",
    colors: ["#052e16", "#16a34a", "#bbf7d0"],
  },
  {
    gradient: "from-fuchsia-50 via-white to-pink-50",
    glow: "bg-fuchsia-300",
    mark: "text-fuchsia-700",
    markBg: "bg-fuchsia-50",
    colors: ["#4a044e", "#c026d3", "#f5d0fe"],
  },
];

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function fetchProjects() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(`${API}/projects`, {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error("Failed to fetch projects");
      }

      const data = await response.json();

      setProjects(data.projects ?? []);
    } catch (caughtError) {
      console.error(caughtError);

      setError(
        "We couldn't load your projects. Make sure the backend is running and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchProjects();
  }, []);

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f7f7fb] text-zinc-900">
      {/* Ambient background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -left-52 top-20 h-[600px] w-[600px] rounded-full bg-violet-300/20 blur-[140px]" />

        <div className="absolute -right-52 top-[280px] h-[620px] w-[620px] rounded-full bg-blue-200/25 blur-[150px]" />

        <div className="absolute bottom-[-300px] left-[35%] h-[600px] w-[650px] rounded-full bg-fuchsia-200/15 blur-[150px]" />
      </div>

      {/* Header */}
      <header className="relative z-30 border-b border-white/70 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-950 text-sm font-bold text-white shadow-sm">
              B
            </div>

            <span className="text-[15px] font-semibold tracking-tight">
              BrandAI
            </span>
          </Link>

          <nav className="flex items-center gap-2">
            <Link
              href="/"
              className="hidden rounded-lg px-3 py-2 text-sm font-medium text-zinc-500 transition hover:bg-white hover:text-zinc-950 sm:inline-flex"
            >
              Home
            </Link>

            <Link
              href="/create"
              className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-zinc-950 px-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-zinc-800"
            >
              <span className="text-base font-normal">+</span>
              New brand
            </Link>
          </nav>
        </div>
      </header>

      {/* Content */}
      <div className="relative z-10 mx-auto max-w-7xl px-6 py-12 lg:px-8">
        {/* Header */}
        <section className="flex flex-col justify-between gap-7 sm:flex-row sm:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-200/80 bg-white/70 px-3 py-1.5 text-xs font-semibold text-violet-700 shadow-sm backdrop-blur">
              <span className="h-1.5 w-1.5 rounded-full bg-violet-500" />
              Brand workspace
            </div>

            <h1 className="mt-5 text-4xl font-semibold tracking-[-0.04em] text-zinc-950 sm:text-5xl">
              Your brands
            </h1>

            <p className="mt-3 max-w-xl text-sm leading-6 text-zinc-500 sm:text-base">
              Manage your identities, explore creative directions and
              continue building your brands.
            </p>
          </div>

          {!loading && !error && projects.length > 0 && (
            <div className="rounded-xl border border-white/80 bg-white/60 px-4 py-3 shadow-sm backdrop-blur">
              <p className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">
                Workspace
              </p>

              <p className="mt-0.5 text-sm font-semibold text-zinc-800">
                {projects.length}{" "}
                {projects.length === 1 ? "brand" : "brands"}
              </p>
            </div>
          )}
        </section>

        {/* Loading */}
        {loading && (
          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="overflow-hidden rounded-[22px] border border-white/80 bg-white/90 shadow-sm"
              >
                <div className="h-40 animate-pulse bg-zinc-100/80" />

                <div className="space-y-4 p-6">
                  <div className="h-5 w-1/2 animate-pulse rounded bg-zinc-100" />

                  <div className="h-3.5 w-full animate-pulse rounded bg-zinc-100" />

                  <div className="h-3.5 w-2/3 animate-pulse rounded bg-zinc-100" />

                  <div className="h-10 animate-pulse rounded-xl bg-zinc-100" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="mt-10 max-w-2xl rounded-[22px] border border-red-100 bg-white/90 p-7 shadow-sm backdrop-blur">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-50 font-bold text-red-600">
              !
            </div>

            <h2 className="mt-4 text-base font-semibold text-zinc-900">
              Couldn&apos;t load your workspace
            </h2>

            <p className="mt-2 text-sm leading-6 text-zinc-500">
              {error}
            </p>

            <button
              type="button"
              onClick={() => void fetchProjects()}
              className="mt-5 rounded-xl bg-zinc-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-zinc-800"
            >
              Try again
            </button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && projects.length === 0 && (
          <div className="mt-10 overflow-hidden rounded-[26px] border border-white/80 bg-white/85 shadow-[0_20px_70px_rgba(79,70,229,0.08)] backdrop-blur-xl">
            <div className="relative flex flex-col items-center px-6 py-20 text-center">
              <div
                aria-hidden="true"
                className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full bg-violet-100/70 blur-[80px]"
              />

              <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-violet-100 bg-violet-50 text-xl font-semibold text-violet-600 shadow-sm">
                ◇
              </div>

              <h2 className="relative mt-6 text-xl font-semibold tracking-tight text-zinc-950">
                Create your first brand
              </h2>

              <p className="relative mt-2 max-w-md text-sm leading-6 text-zinc-500">
                Start with a short business brief and turn your idea
                into a complete visual identity.
              </p>

              <Link
                href="/create"
                className="relative mt-6 inline-flex h-11 items-center gap-2 rounded-xl bg-zinc-950 px-5 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-zinc-800"
              >
                Create brand
                <span>→</span>
              </Link>
            </div>
          </div>
        )}

        {/* Projects */}
        {!loading && !error && projects.length > 0 && (
          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {/* New brand card */}
            <Link
              href="/create"
              className="group relative flex min-h-[365px] flex-col items-center justify-center overflow-hidden rounded-[22px] border border-dashed border-violet-200 bg-white/45 p-8 text-center backdrop-blur transition duration-200 hover:-translate-y-1 hover:border-violet-300 hover:bg-white/70 hover:shadow-[0_18px_50px_rgba(79,70,229,0.08)]"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-violet-50/50 via-transparent to-blue-50/50 opacity-0 transition group-hover:opacity-100" />

              <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl border border-zinc-200 bg-white text-xl text-zinc-500 shadow-sm transition group-hover:border-violet-200 group-hover:text-violet-600">
                +
              </div>

              <p className="relative mt-4 text-sm font-semibold text-zinc-800">
                Create another brand
              </p>

              <p className="relative mt-2 max-w-[220px] text-xs leading-5 text-zinc-400">
                Start a new identity from a simple business brief.
              </p>
            </Link>

            {/* Project cards */}
            {projects.map((project, index) => {
              const theme =
                CARD_THEMES[index % CARD_THEMES.length];

              return (
                <article
                  key={project.id}
                  className="group flex min-h-[365px] flex-col overflow-hidden rounded-[22px] border border-white/90 bg-white/90 shadow-[0_4px_20px_rgba(24,24,27,0.035)] backdrop-blur transition duration-300 hover:-translate-y-1 hover:shadow-[0_22px_60px_rgba(79,70,229,0.10)]"
                >
                  {/* Project visual */}
                  <div
                    className={`relative flex h-40 items-center justify-center overflow-hidden bg-gradient-to-br ${theme.gradient}`}
                  >
                    <div
                      className={`absolute -right-10 -top-10 h-32 w-32 rounded-full ${theme.glow} opacity-20 blur-3xl`}
                    />

                    <div className="absolute inset-0 opacity-[0.025] [background-image:linear-gradient(#000_1px,transparent_1px),linear-gradient(90deg,#000_1px,transparent_1px)] [background-size:18px_18px]" />

                    {/* Fake mark until project API returns thumbnail */}
                    <div
                      className={`relative flex h-20 w-20 items-center justify-center rounded-[22px] border border-white/80 ${theme.markBg} shadow-[0_12px_30px_rgba(0,0,0,0.07)]`}
                    >
                      <span
                        className={`text-3xl font-semibold uppercase tracking-[-0.08em] ${theme.mark}`}
                      >
                        {project.business_name
                          .trim()
                          .slice(0, 1)
                          .toUpperCase() || "B"}
                      </span>
                    </div>

                    {/* Palette */}
                    <div className="absolute bottom-3 right-3 flex -space-x-1">
                      {theme.colors.map((color) => (
                        <div
                          key={color}
                          className="h-6 w-6 rounded-full border-2 border-white shadow-sm"
                          style={{
                            backgroundColor: color,
                          }}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Project info */}
                  <div className="flex flex-1 flex-col p-5">
                    <h2 className="truncate text-lg font-semibold tracking-tight text-zinc-950">
                      {project.business_name}
                    </h2>

                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-[10px] font-medium text-zinc-500">
                        {formatLabel(project.industry)}
                      </span>

                      <span className="rounded-full bg-violet-50 px-2.5 py-1 text-[10px] font-medium text-violet-600">
                        {formatLabel(project.style)}
                      </span>
                    </div>

                    <p className="mt-4 line-clamp-2 text-sm leading-6 text-zinc-500">
                      {project.description}
                    </p>

                    <div className="mt-auto flex items-end justify-between gap-4 border-t border-zinc-100 pt-4">
                      <p className="text-[11px] text-zinc-400">
                        {formatDate(project.created_at)}
                      </p>

                      <Link
                        href={`/projects/${project.id}`}
                        className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-zinc-950 px-3.5 text-xs font-semibold text-white transition hover:bg-zinc-800"
                      >
                        Open studio
                        <span>→</span>
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="relative z-10 mt-12 border-t border-white/70 bg-white/50 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 text-xs text-zinc-400 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-zinc-950 text-[9px] font-bold text-white">
              B
            </div>

            <span>BrandAI Studio</span>
          </div>

          <span>
            {projects.length}{" "}
            {projects.length === 1 ? "project" : "projects"}
          </span>
        </div>
      </footer>
    </main>
  );
}
