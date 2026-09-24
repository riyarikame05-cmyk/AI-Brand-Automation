"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Project = {
  id: string;
  business_name: string;
  description: string;
  industry: string;
  style: string;
  created_at?: string;
};

type Asset = {
  id: string;
  project_id: string;
  asset_type: string;
  url: string;
  prompt?: string;
  is_selected?: boolean;
  created_at?: string;
  palette?: {
    primary_color?: string;
    secondary_color?: string;
    accent_color?: string;
  } | null;
};

type BrandKit = {
  id?: string;
  project_id?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  slogan?: string;
  personality?: string[];
  tone?: string;
  target_audience?: string;
  marketing_message?: string;
  heading_font?: string;
  body_font?: string;
};

const campaignIdeas = [
  {
    title: "Social Media Post",
    icon: "✦",
    description: "Create a polished square social media campaign.",
    prompt:
      "Create a premium square social media campaign visual. Use the brand identity, clean composition, strong visual hierarchy, modern lighting, and professional advertising style.",
  },
  {
    title: "Product Ad",
    icon: "◈",
    description: "Generate a premium advertising visual.",
    prompt:
      "Create a premium product advertising visual for this brand. Modern commercial photography style, sophisticated composition, dramatic but clean lighting, brand-consistent colors, high-end advertising aesthetic.",
  },
  {
    title: "Launch Campaign",
    icon: "🚀",
    description: "Create an energetic brand-launch campaign.",
    prompt:
      "Create an exciting brand launch campaign visual. Bold modern composition, premium branding, confident visual hierarchy, energetic presentation, brand-consistent colors, professional marketing aesthetic.",
  },
  {
    title: "Minimal Campaign",
    icon: "◇",
    description: "Generate a clean, minimal marketing visual.",
    prompt:
      "Create a minimal premium marketing campaign visual. Lots of intentional negative space, elegant geometry, clean background, sophisticated brand colors, editorial advertising aesthetic.",
  },
  {
    title: "Technology Campaign",
    icon: "⌁",
    description: "Create a futuristic technology-focused campaign.",
    prompt:
      "Create a sophisticated technology campaign visual. Futuristic atmosphere, subtle digital elements, modern lighting, premium composition, clean technology aesthetic, brand-consistent colors.",
  },
  {
    title: "Luxury Campaign",
    icon: "◆",
    description: "Create an elegant high-end campaign.",
    prompt:
      "Create an elegant luxury advertising campaign visual. Refined composition, premium materials, sophisticated lighting, restrained details, high-end editorial aesthetic, brand-consistent color palette.",
  },
];

function getErrorMessage(data: any, fallback: string) {
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (typeof data?.message === "string") {
    return data.message;
  }

  return fallback;
}

export default function ProjectToolsPage() {
  const params = useParams();
  const router = useRouter();

  const projectId = String(params?.id || "");

  const [project, setProject] = useState<Project | null>(null);
  const [brandKit, setBrandKit] = useState<BrandKit | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);

  const [prompt, setPrompt] = useState("");
  const [selectedIdea, setSelectedIdea] = useState("");

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const campaignAssets = useMemo(
    () =>
      assets.filter(
        (asset) => asset.asset_type === "campaign_image"
      ),
    [assets]
  );

  const selectedLogo = useMemo(
    () =>
      assets.find(
        (asset) =>
          asset.asset_type === "logo" &&
          asset.is_selected
      ),
    [assets]
  );

  const videos = useMemo(
    () =>
      assets.filter(
        (asset) => asset.asset_type === "video"
      ),
    [assets]
  );

  async function loadData() {
    if (!projectId) return;

    setLoading(true);
    setError("");

    try {
      const [projectResponse, assetsResponse, kitResponse] =
        await Promise.all([
          fetch(`${API_URL}/projects/${projectId}`, {
            cache: "no-store",
          }),
          fetch(`${API_URL}/projects/${projectId}/assets`, {
            cache: "no-store",
          }),
          fetch(`${API_URL}/projects/${projectId}/brand-kit`, {
            cache: "no-store",
          }),
        ]);

      if (!projectResponse.ok) {
        const data = await projectResponse
          .json()
          .catch(() => ({}));

        throw new Error(
          getErrorMessage(
            data,
            "Could not load project."
          )
        );
      }

      const projectData = await projectResponse.json();

      setProject(projectData.project || null);

      if (assetsResponse.ok) {
        const assetsData = await assetsResponse.json();

        setAssets(
          Array.isArray(assetsData.assets)
            ? assetsData.assets
            : []
        );
      }

      if (kitResponse.ok) {
        const kitData = await kitResponse.json();

        setBrandKit(kitData.brand_kit || null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load project tools."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [projectId]);

  function useCampaignIdea(
    title: string,
    ideaPrompt: string
  ) {
    setSelectedIdea(title);
    setPrompt(ideaPrompt);
    setError("");
  }

  async function generateCampaign() {
    const finalPrompt = prompt.trim();

    if (!finalPrompt) {
      setError(
        "Choose a campaign idea or enter your own prompt."
      );
      return;
    }

    setGenerating(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/projects/${projectId}/generate-image`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            prompt: finalPrompt,
            provider: "auto",
          }),
        }
      );

      const data = await response
        .json()
        .catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data,
            "Campaign image generation failed."
          )
        );
      }

      if (data.asset) {
        setAssets((current) => [
          data.asset,
          ...current.filter(
            (asset) => asset.id !== data.asset.id
          ),
        ]);
      } else {
        await loadData();
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Campaign image generation failed."
      );
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-[#f7f7fb] text-zinc-950">
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-5 h-10 w-10 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />

            <p className="text-sm text-zinc-500">
              Loading brand tools...
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f7f7fb] text-zinc-950">
      {/* Header */}

      <header className="border-b border-zinc-200/80 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <button
            onClick={() =>
              router.push(`/projects/${projectId}`)
            }
            className="flex items-center gap-2 text-sm font-medium text-zinc-500 transition hover:text-zinc-950"
          >
            <span>←</span>
            Back to project
          </button>

          <div className="rounded-full border border-violet-200 bg-violet-50 px-4 py-1.5 text-xs font-semibold text-violet-700">
            BrandAI Tools
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-12">
        {/* Intro */}

        <section className="mb-10">
          <div className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-violet-600">
            Creative Studio
          </div>

          <h1 className="text-4xl font-bold tracking-tight text-zinc-950 sm:text-5xl">
            {project?.business_name || "Brand"} Tools
          </h1>

          <p className="mt-4 max-w-3xl text-base leading-7 text-zinc-500">
            Turn your brand identity into campaign visuals,
            marketing assets, and downloadable creative material.
            BrandAI can use online generation while retaining your
            local generation fallback.
          </p>
        </section>

        {/* Error */}

        {error && (
          <div className="mb-8 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">
            {error}
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-8">
            {/* Generator */}

            <section className="rounded-[28px] border border-zinc-200/80 bg-white p-7 shadow-[0_12px_40px_rgba(24,24,27,0.05)]">
              <div className="mb-7">
                <div className="mb-2 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-lg text-violet-700">
                    ✦
                  </div>

                  <h2 className="text-2xl font-bold tracking-tight">
                    AI Campaign Generator
                  </h2>
                </div>

                <p className="ml-[52px] text-sm leading-6 text-zinc-500">
                  Choose a starting point, customize the prompt,
                  then generate a brand-aware campaign image.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {campaignIdeas.map((idea) => {
                  const active =
                    selectedIdea === idea.title;

                  return (
                    <button
                      key={idea.title}
                      type="button"
                      onClick={() =>
                        useCampaignIdea(
                          idea.title,
                          idea.prompt
                        )
                      }
                      className={`group rounded-2xl border p-5 text-left transition ${
                        active
                          ? "border-violet-500 bg-violet-50 shadow-sm ring-2 ring-violet-100"
                          : "border-zinc-200 bg-white hover:-translate-y-0.5 hover:border-violet-300 hover:shadow-md"
                      }`}
                    >
                      <div
                        className={`mb-5 flex h-11 w-11 items-center justify-center rounded-xl text-lg ${
                          active
                            ? "bg-violet-600 text-white"
                            : "bg-violet-50 text-violet-700"
                        }`}
                      >
                        {idea.icon}
                      </div>

                      <div className="font-semibold text-zinc-950">
                        {idea.title}
                      </div>

                      <div className="mt-2 text-xs leading-5 text-zinc-500">
                        {idea.description}
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="mt-8">
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-sm font-semibold text-zinc-800">
                    Campaign prompt
                  </label>

                  <span className="text-xs text-zinc-400">
                    {prompt.length} characters
                  </span>
                </div>

                <textarea
                  value={prompt}
                  onChange={(event) =>
                    setPrompt(event.target.value)
                  }
                  rows={5}
                  placeholder="Describe the marketing visual you want to create..."
                  className="w-full resize-none rounded-2xl border border-zinc-200 bg-[#fafafa] px-4 py-4 text-sm leading-6 text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-violet-400 focus:bg-white focus:ring-4 focus:ring-violet-100"
                />

                <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-xs font-medium text-zinc-500">
                      Hybrid generation
                    </p>

                    <p className="mt-1 text-xs text-zinc-400">
                      Online provider → local fallback
                    </p>
                  </div>

                  <button
                    type="button"
                    disabled={
                      generating || !prompt.trim()
                    }
                    onClick={generateCampaign}
                    className="min-w-[190px] rounded-xl bg-zinc-950 px-6 py-3.5 text-sm font-semibold text-white shadow-lg transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {generating
                      ? "Generating..."
                      : "Generate Campaign"}
                  </button>
                </div>

                {generating && (
                  <div className="mt-5 rounded-2xl border border-violet-100 bg-violet-50 p-4">
                    <div className="flex items-center gap-3">
                      <div className="h-5 w-5 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />

                      <div>
                        <p className="text-sm font-semibold text-violet-900">
                          Creating your campaign
                        </p>

                        <p className="mt-0.5 text-xs text-violet-600">
                          Online generation will automatically
                          fall back locally if necessary.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </section>

            {/* Gallery */}

            <section className="rounded-[28px] border border-zinc-200/80 bg-white p-7 shadow-[0_12px_40px_rgba(24,24,27,0.05)]">
              <div className="mb-7 flex items-center justify-between gap-4">
                <div>
                  <div className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-violet-600">
                    Creative Assets
                  </div>

                  <h2 className="text-2xl font-bold tracking-tight">
                    Campaign Gallery
                  </h2>

                  <p className="mt-2 text-sm text-zinc-500">
                    Generated marketing visuals for this brand.
                  </p>
                </div>

                <div className="rounded-full border border-zinc-200 bg-zinc-50 px-4 py-2 text-xs font-semibold text-zinc-600">
                  {campaignAssets.length}{" "}
                  {campaignAssets.length === 1
                    ? "image"
                    : "images"}
                </div>
              </div>

              {campaignAssets.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-zinc-300 bg-zinc-50/70 px-6 py-16 text-center">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100 text-2xl text-violet-700">
                    ✦
                  </div>

                  <p className="font-semibold text-zinc-900">
                    No campaign images yet
                  </p>

                  <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-zinc-500">
                    Choose one of the campaign styles above or
                    write your own creative prompt to generate
                    the first visual.
                  </p>
                </div>
              ) : (
                <div className="grid gap-6 sm:grid-cols-2">
                  {campaignAssets.map((asset) => (
                    <article
                      key={asset.id}
                      className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
                    >
                      <div className="aspect-square overflow-hidden bg-zinc-100">
                        <img
                          src={asset.url}
                          alt={
                            asset.prompt ||
                            "Generated campaign"
                          }
                          className="h-full w-full object-cover"
                        />
                      </div>

                      <div className="p-5">
                        <p className="line-clamp-2 min-h-10 text-sm leading-5 text-zinc-500">
                          {asset.prompt ||
                            "AI-generated campaign image"}
                        </p>

                        <div className="mt-5 flex gap-3">
                          <a
                            href={asset.url}
                            target="_blank"
                            rel="noreferrer"
                            className="flex-1 rounded-xl border border-zinc-200 px-3 py-2.5 text-center text-xs font-semibold text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
                          >
                            Open
                          </a>

                          <a
                            href={asset.url}
                            download
                            className="flex-1 rounded-xl bg-zinc-950 px-3 py-2.5 text-center text-xs font-semibold text-white transition hover:bg-violet-700"
                          >
                            Download
                          </a>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </div>

          {/* Sidebar */}

          <aside className="space-y-6">
            {/* Brand Identity */}

            <section className="rounded-[28px] border border-zinc-200/80 bg-white p-6 shadow-[0_12px_40px_rgba(24,24,27,0.05)]">
              <div className="mb-5">
                <div className="text-xs font-bold uppercase tracking-[0.16em] text-violet-600">
                  Your Brand
                </div>

                <h2 className="mt-2 text-lg font-bold">
                  Brand Identity
                </h2>
              </div>

              {selectedLogo ? (
                <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white p-4">
                  <img
                    src={selectedLogo.url}
                    alt="Selected logo"
                    className="aspect-square h-auto w-full object-contain"
                  />
                </div>
              ) : (
                <div className="flex aspect-square items-center justify-center rounded-2xl border border-dashed border-zinc-300 bg-zinc-50 text-center">
                  <div>
                    <div className="text-2xl text-zinc-300">
                      ◇
                    </div>
                    <p className="mt-2 text-xs text-zinc-500">
                      No selected logo
                    </p>
                  </div>
                </div>
              )}

              <div className="mt-5">
                <div className="text-lg font-bold">
                  {project?.business_name}
                </div>

                <div className="mt-1 text-xs font-medium text-zinc-400">
                  {project?.industry}
                  {project?.style
                    ? ` · ${project.style}`
                    : ""}
                </div>

                {brandKit?.slogan && (
                  <p className="mt-4 border-l-2 border-violet-400 pl-3 text-sm italic leading-6 text-zinc-500">
                    “{brandKit.slogan}”
                  </p>
                )}
              </div>
            </section>

            {/* Colors */}

            <section className="rounded-[28px] border border-zinc-200/80 bg-white p-6 shadow-[0_12px_40px_rgba(24,24,27,0.05)]">
              <div className="mb-5">
                <div className="text-xs font-bold uppercase tracking-[0.16em] text-violet-600">
                  Identity System
                </div>

                <h2 className="mt-2 text-lg font-bold">
                  Brand Colors
                </h2>
              </div>

              <div className="space-y-3">
                {[
                  {
                    label: "Primary",
                    value:
                      brandKit?.primary_color ||
                      "#111827",
                  },
                  {
                    label: "Secondary",
                    value:
                      brandKit?.secondary_color ||
                      "#6366F1",
                  },
                  {
                    label: "Accent",
                    value:
                      brandKit?.accent_color ||
                      "#8B5CF6",
                  },
                ].map((color) => (
                  <button
                    key={color.label}
                    type="button"
                    onClick={() => {
                      navigator.clipboard
                        ?.writeText(color.value)
                        .catch(() => {});
                    }}
                    className="flex w-full items-center justify-between rounded-2xl border border-zinc-200 bg-white p-3 text-left transition hover:border-violet-300 hover:bg-violet-50/30"
                    title="Click to copy"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="h-10 w-10 rounded-xl border border-black/5 shadow-sm"
                        style={{
                          backgroundColor:
                            color.value,
                        }}
                      />

                      <div>
                        <div className="text-xs text-zinc-400">
                          {color.label}
                        </div>

                        <div className="mt-0.5 font-mono text-sm font-semibold text-zinc-800">
                          {color.value}
                        </div>
                      </div>
                    </div>

                    <span className="text-xs font-medium text-zinc-400">
                      Copy
                    </span>
                  </button>
                ))}
              </div>
            </section>

            {/* Assets */}

            <section className="rounded-[28px] border border-zinc-200/80 bg-white p-6 shadow-[0_12px_40px_rgba(24,24,27,0.05)]">
              <div className="mb-5">
                <div className="text-xs font-bold uppercase tracking-[0.16em] text-violet-600">
                  Project Files
                </div>

                <h2 className="mt-2 text-lg font-bold">
                  Brand Assets
                </h2>
              </div>

              <div className="divide-y divide-zinc-100 rounded-2xl border border-zinc-200">
                <div className="flex items-center justify-between p-4 text-sm">
                  <span className="text-zinc-500">
                    Campaign images
                  </span>

                  <span className="font-bold text-zinc-900">
                    {campaignAssets.length}
                  </span>
                </div>

                <div className="flex items-center justify-between p-4 text-sm">
                  <span className="text-zinc-500">
                    Videos
                  </span>

                  <span className="font-bold text-zinc-900">
                    {videos.length}
                  </span>
                </div>
              </div>

              <a
                href={`${API_URL}/projects/${projectId}/download-package`}
                className="mt-5 block w-full rounded-xl bg-zinc-950 px-4 py-3.5 text-center text-sm font-semibold text-white transition hover:bg-violet-700"
              >
                Download Brand Package
              </a>
            </section>

            {/* Video */}

            {videos.length > 0 && (
              <section className="rounded-[28px] border border-zinc-200/80 bg-white p-6 shadow-[0_12px_40px_rgba(24,24,27,0.05)]">
                <div className="mb-4">
                  <div className="text-xs font-bold uppercase tracking-[0.16em] text-violet-600">
                    Brand Motion
                  </div>

                  <h2 className="mt-2 text-lg font-bold">
                    Latest Video
                  </h2>
                </div>

                <video
                  controls
                  src={videos[0].url}
                  className="w-full rounded-2xl bg-black"
                />

                <a
                  href={videos[0].url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 block text-center text-xs font-semibold text-violet-600 hover:text-violet-800"
                >
                  Open video
                </a>
              </section>
            )}
          </aside>
        </div>
      </div>
    </main>
  );
}