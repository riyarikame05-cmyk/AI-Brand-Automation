"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Project = {
  id: string;
  business_name: string;
  description: string;
  industry: string;
  style: string;
  created_at: string;
};

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchProjects() {
      try {
        const response = await fetch("http://127.0.0.1:8000/projects");

        if (!response.ok) {
          throw new Error("Failed to fetch projects");
        }

        const data = await response.json();

        setProjects(data.projects);
      } catch (error) {
        console.error(error);
        setError("Could not load projects from backend.");
      } finally {
        setLoading(false);
      }
    }

    fetchProjects();
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-slate-800 px-8 py-5">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Link href="/" className="text-2xl font-bold text-violet-400">
            BrandAI
          </Link>

          <div className="flex items-center gap-6">
            <Link href="/" className="text-slate-400 hover:text-white">
              Home
            </Link>

            <Link
              href="/create"
              className="rounded-lg bg-violet-600 px-4 py-2 font-medium transition hover:bg-violet-500"
            >
              New Brand
            </Link>
          </div>
        </div>
      </nav>

      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="mb-10 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <p className="mb-2 text-sm font-semibold text-violet-400">
              DASHBOARD
            </p>

            <h1 className="text-4xl font-bold">
              My Brand Projects
            </h1>

            <p className="mt-3 text-slate-400">
              View all brand projects saved in your PostgreSQL database.
            </p>
          </div>

          <Link
            href="/create"
            className="rounded-xl bg-violet-600 px-5 py-3 text-center font-semibold transition hover:bg-violet-500"
          >
            + Create New Brand
          </Link>
        </div>

        {loading && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-400">
            Loading projects...
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-800 bg-red-950/40 p-8 text-red-300">
            {error}
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
            <h2 className="text-2xl font-semibold">
              No projects found
            </h2>

            <p className="mt-3 text-slate-400">
              Create your first brand project to see it here.
            </p>

            <Link
              href="/create"
              className="mt-6 inline-block rounded-lg bg-violet-600 px-5 py-3 font-semibold transition hover:bg-violet-500"
            >
              Create Brand
            </Link>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <div
                key={project.id}
                className="rounded-2xl border border-slate-800 bg-slate-900 p-6 transition hover:border-violet-500/60"
              >
                <div className="mb-4">
                  <h2 className="text-2xl font-bold text-white">
                    {project.business_name}
                  </h2>

                  <p className="mt-1 text-sm text-violet-400">
                    {project.industry}
                  </p>
                </div>

                <p className="mb-5 line-clamp-3 text-slate-400">
                  {project.description}
                </p>

                <div className="mb-5 flex items-center justify-between rounded-lg bg-slate-950 px-4 py-3">
                  <span className="text-sm text-slate-500">
                    Style
                  </span>

                  <span className="font-medium text-slate-200">
                    {project.style}
                  </span>
                </div>

                <p className="mb-5 text-xs text-slate-500">
                  Created:{" "}
                  {new Date(project.created_at).toLocaleString()}
                </p>

                <Link
                  href={`/projects/${project.id}`}
                  className="block w-full rounded-lg border border-slate-700 px-4 py-3 text-center font-medium text-slate-300 transition hover:border-violet-500 hover:text-white"
                >
                  View Project
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}