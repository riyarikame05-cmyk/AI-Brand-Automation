"use client";

import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import BrandScorePanel from "../../components/BrandScorePanel";

const API =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

// ======================================================
// TYPES
// ======================================================

interface Project {
  id: string;
  business_name: string;
  description: string;
  industry: string;
  style: string;
  generation_palette?: string;
  generation_custom_colors?: string[];
  generation_logo_style?: string;
  generation_creative_prompt?: string;
  created_at: string;
}

interface Palette {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
}

interface Asset {
  id: string;
  project_id: string;
  asset_type: string;
  url: string;
  prompt: string | null;
  specification?: {
    primary_color?: string;
    secondary_color?: string;
    accent_color?: string;
    logo_type?: string;
    shape?: string;
    creative_direction?: string;
    [key: string]: unknown;
  } | null;
  is_selected: boolean;
  created_at: string;
  palette?: Palette | null;
}

interface BrandKit {
  id: string;
  project_id: string;

  primary_color: string;
  secondary_color: string;
  accent_color: string;

  slogan: string | null;
  personality: string[];
  tone: string | null;
  target_audience: string | null;
  marketing_message: string | null;

  heading_font: string | null;
  body_font: string | null;

  created_at: string;
}

interface ProjectResponse {
  project: Project;
}

interface AssetsResponse {
  assets: Asset[];
}

interface BrandKitResponse {
  brand_kit: BrandKit | null;
}

interface GenerateLogoResponse {
  concepts: Asset[];
}

interface SelectLogoResponse {
  brand_kit: BrandKit;
  video?: Asset | null;
}

interface RefineLogoResponse {
  message: string;
  source_logo_id: string;
  revision_number: number;
  logo: Asset;
}

// ======================================================
// DESIGN DIRECTIONS
// ======================================================

const DIRECTIONS = [
  {
    name: "Minimal Geometric",
    description: "Clean geometry with a strong, scalable silhouette.",
  },
  {
    name: "Negative Space",
    description: "A concept built around purposeful hidden space.",
  },
  {
    name: "Monogram",
    description: "A recognizable mark based on your brand initials.",
  },
  {
    name: "Abstract Motion",
    description: "A dynamic symbol expressing progress and movement.",
  },
  {
    name: "Wordmark",
    description: "A typography-led identity focused on the brand name.",
  },
  {
    name: "Brand Emblem",
    description: "A compact identity designed for versatile brand use.",
  },
];

// ======================================================
// HELPERS
// ======================================================

function getAssetUrl(url: string) {
  if (!url) return "";

  if (
    url.startsWith("http://") ||
    url.startsWith("https://") ||
    url.startsWith("data:") ||
    url.startsWith("blob:")
  ) {
    return url;
  }

  return `${API}${url.startsWith("/") ? "" : "/"}${url}`;
}

function formatLabel(value?: string | null) {
  if (!value) return "";

  return value
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function safeColor(color?: string | null, fallback = "#18181B") {
  return color || fallback;
}

function isNearWhite(color?: string | null) {
  if (!color) return true;

  const normalized = color.trim().replace("#", "");

  if (!/^[0-9a-fA-F]{6}$/.test(normalized)) {
    return false;
  }

  const red = parseInt(normalized.slice(0, 2), 16);
  const green = parseInt(normalized.slice(2, 4), 16);
  const blue = parseInt(normalized.slice(4, 6), 16);

  const luminance =
    0.2126 * red +
    0.7152 * green +
    0.0722 * blue;

  return luminance > 225;
}

function cleanPalette(palette?: Palette | null): Palette | null {
  if (!palette) return null;

  const fallback = [
    "#18181B",
    "#6D5DFC",
    "#8B5CF6",
  ];

  const source = [
    palette.primary_color,
    palette.secondary_color,
    palette.accent_color,
  ];

  const useful = source.filter(
    (color) => color && !isNearWhite(color)
  );

  const result: string[] = [];

  useful.forEach((color) => {
    if (!result.includes(color.toUpperCase())) {
      result.push(color.toUpperCase());
    }
  });

  fallback.forEach((color) => {
    if (
      result.length < 3 &&
      !result.includes(color)
    ) {
      result.push(color);
    }
  });

  return {
    primary_color: result[0],
    secondary_color: result[1],
    accent_color: result[2],
  };
}

function getDirection(index: number) {
  return DIRECTIONS[index % DIRECTIONS.length];
}

function dateValue(value?: string) {
  if (!value) return 0;

  const timestamp = new Date(value).getTime();

  return Number.isNaN(timestamp)
    ? 0
    : timestamp;
}

// ======================================================
// PAGE
// ======================================================

export default function ProjectPage() {
  const params = useParams<{ id: string }>();
  const projectId = params?.id;

  const [project, setProject] =
    useState<Project | null>(null);

  const [assets, setAssets] =
    useState<Asset[]>([]);

  const [brandKit, setBrandKit] =
    useState<BrandKit | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [generating, setGenerating] =
    useState(false);

  const [selectingLogo, setSelectingLogo] =
    useState<string | null>(null);

  const [refiningLogo, setRefiningLogo] =
    useState(false);

  const [refinePrimary, setRefinePrimary] =
    useState("");

  const [refineSecondary, setRefineSecondary] =
    useState("");

  const [refineAccent, setRefineAccent] =
    useState("");

  const [refineTypography, setRefineTypography] =
    useState("modern");

  const [refineLayout, setRefineLayout] =
    useState("horizontal");

  const [refineBackground, setRefineBackground] =
    useState("light");

  const [refineTreatment, setRefineTreatment] =
    useState("premium-gradient");

  const [refineInstruction, setRefineInstruction] =
    useState("");

  const [latestRefinementId, setLatestRefinementId] =
    useState<string | null>(null);

  const [error, setError] =
    useState("");

  const [successMessage, setSuccessMessage] =
    useState("");
    

  // ======================================================
  // ERROR HELPER
  // ======================================================

  const getErrorMessage = async (
    response: Response,
    fallback: string
  ): Promise<string> => {
    try {
      const text = await response.text();

      if (!text) return fallback;

      const data = JSON.parse(text);

      return (
        data?.detail ||
        data?.message ||
        fallback
      );
    } catch {
      return fallback;
    }
  };

  // ======================================================
  // LOAD
  // ======================================================

  const loadData = useCallback(
    async (showLoader = true) => {
      if (!projectId) return;

      try {
        if (showLoader) {
          setLoading(true);
        }

        setError("");

        const [
          projectResponse,
          assetsResponse,
          brandKitResponse,
        ] = await Promise.all([
          fetch(
            `${API}/projects/${projectId}`,
            {
              cache: "no-store",
            }
          ),

          fetch(
            `${API}/projects/${projectId}/assets`,
            {
              cache: "no-store",
            }
          ),

          fetch(
            `${API}/projects/${projectId}/brand-kit`,
            {
              cache: "no-store",
            }
          ),
        ]);

        if (!projectResponse.ok) {
          throw new Error(
            await getErrorMessage(
              projectResponse,
              "Could not load project."
            )
          );
        }

        if (!assetsResponse.ok) {
          throw new Error(
            await getErrorMessage(
              assetsResponse,
              "Could not load assets."
            )
          );
        }

        if (!brandKitResponse.ok) {
          throw new Error(
            await getErrorMessage(
              brandKitResponse,
              "Could not load brand kit."
            )
          );
        }

        const projectData: ProjectResponse =
          await projectResponse.json();

        const assetsData: AssetsResponse =
          await assetsResponse.json();

        const brandKitData: BrandKitResponse =
          await brandKitResponse.json();

        setProject(
          projectData.project
        );

        setAssets(
          assetsData.assets ?? []
        );

        setBrandKit(
          brandKitData.brand_kit ?? null
        );
      } catch (err) {
        console.error(
          "Load project error:",
          err
        );

        setError(
          err instanceof Error
            ? err.message
            : "Could not load project."
        );
      } finally {
        if (showLoader) {
          setLoading(false);
        }
      }
    },
    [projectId]
  );

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // ======================================================
  // GENERATE MORE
  // ======================================================

  async function generateMore() {
    if (
      !projectId ||
      generating ||
      selectingLogo
    ) {
      return;
    }

    try {
      setGenerating(true);
      setError("");
      setSuccessMessage("");

      const response = await fetch(
        `${API}/projects/${projectId}/generate-logo`,
        {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            count: 3,
            logo_style:
              project?.generation_logo_style ||
              project?.style ||
              "",
            palette:
              project?.generation_palette ||
              "",
            custom_colors:
              project?.generation_custom_colors ||
              [],
            creative_prompt: "",
          }),
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          await getErrorMessage(
            response,
            "Could not generate logo concepts."
          )
        );
      }

      const data: GenerateLogoResponse =
        await response.json();

      const concepts =
        data.concepts ?? [];

      if (concepts.length === 0) {
        throw new Error(
          "The server returned no logo concepts."
        );
      }

      // Reload because backend asset ordering is newest first.
      // We sort explicitly below.
      await loadData(false);

      setSuccessMessage(
        `${concepts.length} new logo concept${
          concepts.length === 1
            ? ""
            : "s"
        } created locally.`
      );
    } catch (err) {
      console.error(
        "Generate logo error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Logo generation failed."
      );
    } finally {
      setGenerating(false);
    }
  }

  // ======================================================
  // SELECT LOGO
  // ======================================================

  async function selectLogo(
    logoId: string
  ) {
    if (
      !projectId ||
      selectingLogo ||
      generating
    ) {
      return;
    }

    try {
      setSelectingLogo(logoId);
      setError("");
      setSuccessMessage("");

      const response = await fetch(
        `${API}/projects/${projectId}/logos/${logoId}/select`,
        {
          method: "POST",
          headers: {
            Accept: "application/json",
          },
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          await getErrorMessage(
            response,
            "Could not select logo."
          )
        );
      }

      const data: SelectLogoResponse =
        await response.json();

      setBrandKit(
        data.brand_kit
      );

      await loadData(false);

      setSuccessMessage(
        data.video
          ? "Brand identity and promotional video created."
          : "Brand identity created successfully."
      );
    } catch (err) {
      console.error(
        "Select logo error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Could not select logo."
      );
    } finally {
      setSelectingLogo(null);
    }
  }

  // ======================================================
  // REFINE LOGO
  // ======================================================

  async function refineSelectedLogo() {
    if (
      !projectId ||
      !selectedLogo ||
      refiningLogo ||
      selectingLogo ||
      generating
    ) {
      return;
    }

    try {
      setRefiningLogo(true);
      setError("");
      setSuccessMessage("");

      const response = await fetch(
        `${API}/projects/${projectId}/logos/${selectedLogo.id}/refine`,
        {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            primary_color: refinePrimary,
            secondary_color: refineSecondary,
            accent_color: refineAccent,
            typography_personality: refineTypography,
            presentation_layout: refineLayout,
            background_mode: refineBackground,
            treatment: refineTreatment,
            instruction: refineInstruction,
          }),
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          await getErrorMessage(
            response,
            "Could not refine logo."
          )
        );
      }

      const data: RefineLogoResponse =
        await response.json();

      setLatestRefinementId(data.logo.id);

      await loadData(false);

      setSuccessMessage(
        `Logo refinement ${data.revision_number} created. Compare it below before selecting it.`
      );
    } catch (err) {
      console.error(
        "Logo refinement error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Could not refine logo."
      );
    } finally {
      setRefiningLogo(false);
    }
  }

  // ======================================================
  // DERIVED DATA
  // ======================================================

  const logos = useMemo(() => {
    return assets
      .filter(
        (asset) =>
          asset.asset_type === "logo"
      )
      .slice()
      .sort(
        (a, b) =>
          dateValue(a.created_at) -
          dateValue(b.created_at)
      );
  }, [assets]);

  const videos = useMemo(() => {
    return assets
      .filter(
        (asset) =>
          asset.asset_type === "video"
      )
      .slice()
      .sort(
        (a, b) =>
          dateValue(a.created_at) -
          dateValue(b.created_at)
      );
  }, [assets]);

  const selectedLogo =
    logos.find(
      (logo) => logo.is_selected
    ) ?? null;

  const latestRefinement =
    latestRefinementId
      ? logos.find(
          (logo) =>
            logo.id === latestRefinementId
        ) ?? null
      : null;

  const latestVideo =
    videos.length > 0
      ? videos[videos.length - 1]
      : null;

  useEffect(() => {
    if (!selectedLogo) return;

    const spec =
      selectedLogo.specification || {};

    setRefinePrimary(
      typeof spec.primary_color === "string"
        ? spec.primary_color
        : ""
    );

    setRefineSecondary(
      typeof spec.secondary_color === "string"
        ? spec.secondary_color
        : ""
    );

    setRefineAccent(
      typeof spec.accent_color === "string"
        ? spec.accent_color
        : ""
    );

    setRefineTypography(
      typeof spec.typography_personality === "string"
        ? spec.typography_personality
        : "modern"
    );

    setRefineLayout(
      typeof spec.presentation_layout === "string"
        ? spec.presentation_layout
        : "horizontal"
    );

    setRefineBackground(
      typeof spec.background_mode === "string"
        ? spec.background_mode
        : "light"
    );

    setRefineTreatment(
      typeof spec.treatment === "string"
        ? spec.treatment
        : "premium-gradient"
    );
  }, [selectedLogo]);

  const displayedBrandPalette =
    useMemo(() => {
      if (!brandKit) return null;

      return cleanPalette({
        primary_color:
          brandKit.primary_color,
        secondary_color:
          brandKit.secondary_color,
        accent_color:
          brandKit.accent_color,
      });
    }, [brandKit]);

  // ======================================================
  // LOADING
  // ======================================================

  if (loading) {
    return (
      <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#f7f7fb]">
        <div className="absolute -left-40 top-20 h-[500px] w-[500px] rounded-full bg-violet-300/20 blur-[130px]" />

        <div className="absolute -right-40 bottom-10 h-[500px] w-[500px] rounded-full bg-blue-200/25 blur-[130px]" />

        <div className="relative text-center">
          <div className="studio-spinner mx-auto h-9 w-9 rounded-full border-[3px] border-violet-100 border-t-violet-600" />

          <p className="mt-4 text-sm font-medium text-zinc-600">
            Preparing your brand studio...
          </p>

          <p className="mt-1 text-xs text-zinc-400">
            Loading identity and creative assets
          </p>
        </div>
      </main>
    );
  }

  // ======================================================
  // NOT FOUND
  // ======================================================

  if (!project) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f7f7fb] px-6">
        <div className="max-w-md rounded-3xl border border-zinc-200 bg-white p-8 text-center shadow-xl">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-red-50 font-semibold text-red-600">
            !
          </div>

          <h1 className="mt-5 text-xl font-semibold text-zinc-950">
            Project unavailable
          </h1>

          <p className="mt-2 text-sm leading-6 text-zinc-500">
            {error ||
              "This project could not be found."}
          </p>

          <Link
            href="/dashboard"
            className="mt-6 inline-flex rounded-xl bg-zinc-950 px-5 py-2.5 text-sm font-semibold text-white"
          >
            Back to dashboard
          </Link>
        </div>
      </main>
    );
  }

  // ======================================================
  // PAGE
  // ======================================================

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f7f7fb] text-zinc-900">
      {/* Background */}

      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -left-52 top-24 h-[620px] w-[620px] rounded-full bg-violet-300/15 blur-[150px]" />

        <div className="absolute -right-52 top-[500px] h-[650px] w-[650px] rounded-full bg-blue-200/20 blur-[160px]" />

        <div className="absolute bottom-[400px] left-[25%] h-[600px] w-[700px] rounded-full bg-fuchsia-200/10 blur-[160px]" />
      </div>

      {/* Navigation */}

      <header className="sticky top-0 z-40 border-b border-white/80 bg-white/75 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <div className="flex items-center gap-6">
            <Link
              href="/"
              className="flex items-center gap-2.5"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-950 text-sm font-bold text-white">
                B
              </div>

              <span className="hidden text-[15px] font-semibold tracking-tight sm:block">
                BrandAI
              </span>
            </Link>

            <div className="hidden h-5 w-px bg-zinc-200 sm:block" />

            <div className="hidden items-center gap-2 text-sm sm:flex">
              <Link
                href="/dashboard"
                className="text-zinc-400 transition hover:text-zinc-900"
              >
                Projects
              </Link>

              <span className="text-zinc-300">
                /
              </span>

              <span className="max-w-48 truncate font-medium text-zinc-700">
                {project.business_name}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/dashboard"
              className="rounded-lg px-3 py-2 text-sm font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900"
            >
              Dashboard
            </Link>

            <Link
              href="/create"
              className="rounded-lg bg-zinc-950 px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-zinc-800"
            >
              + New brand
            </Link>
          </div>
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-7xl px-6 py-10 lg:px-8">
        {/* Heading */}

        <section className="flex flex-col justify-between gap-7 border-b border-zinc-200/80 pb-9 lg:flex-row lg:items-end">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-zinc-200 bg-white/80 px-3 py-1 text-xs font-medium text-zinc-500 shadow-sm">
                {formatLabel(
                  project.industry
                )}
              </span>

              <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-medium text-violet-700">
                {formatLabel(
                  project.style
                )}
              </span>

              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                Local AI
              </span>

              {selectedLogo && (
                <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                  Ã¢Å“â€œ Identity selected
                </span>
              )}
            </div>

            <h1 className="mt-5 text-4xl font-semibold tracking-[-0.045em] text-zinc-950 sm:text-5xl">
              {project.business_name}
            </h1>

            <p className="mt-4 max-w-3xl text-sm leading-7 text-zinc-500 sm:text-base">
              {project.description}
            </p>
          </div>

                    <div className="flex shrink-0 flex-wrap items-center gap-3">
            <Link
              href={`/projects/${projectId}/tools`}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-violet-700 hover:shadow-md"
            >
              <span>Ã¢Å“Â¦</span>
              Creative Tools
              <span>&rarr;</span>
            </Link>

            <button
              type="button"
              onClick={generateMore}
              disabled={
                generating ||
                selectingLogo !== null
              }
              className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white px-4 text-sm font-semibold text-zinc-700 shadow-sm transition hover:-translate-y-0.5 hover:border-zinc-300 hover:shadow-md disabled:translate-y-0 disabled:opacity-50"
            >
              {generating ? (
                <>
                  <span className="studio-spinner h-4 w-4 rounded-full border-2 border-zinc-200 border-t-violet-600" />
                  Creating concepts...
                </>
              ) : (
                <>
                  <span></span>
                  Generate more
                </>
              )}
            </button>
          </div>
        </section>

        {/* Messages */}

        {(error ||
          successMessage) && (
          <section className="mt-6">
            {error && (
              <div
                role="alert"
                className="rounded-xl border border-red-200 bg-red-50 px-4 py-3.5 text-sm text-red-700"
              >
                {error}
              </div>
            )}

            {successMessage && (
              <div
                role="status"
                className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3.5 text-sm text-emerald-700"
              >
                Ã¢Å“â€œ {successMessage}
              </div>
            )}
          </section>
        )}

        {/* Logo studio */}

        <section className="py-10">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">
                Creative directions
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.025em] text-zinc-950">
                Explore your logo concepts
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-zinc-500">
                Every direction explores a
                different identity approach.
                Choose the strongest fit for
                your business.
              </p>
            </div>

            {logos.length > 0 && (
              <span className="text-xs font-medium text-zinc-400">
                {logos.length} concept
                {logos.length === 1
                  ? ""
                  : "s"}
              </span>
            )}
          </div>

          {generating && (
            <div className="mt-6 overflow-hidden rounded-2xl border border-violet-100 bg-white/80 p-5 shadow-sm">
              <div className="flex items-center gap-4">
                <div className="studio-spinner h-6 w-6 shrink-0 rounded-full border-[3px] border-violet-100 border-t-violet-600" />

                <div>
                  <p className="text-sm font-semibold text-zinc-800">
                    Developing three new
                    directions
                  </p>

                  <p className="mt-1 text-xs leading-5 text-zinc-500">
                    Ollama is creating the
                    design specifications and
                    the local renderer is
                    building your logos.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Logo grid */}

          {logos.length > 0 ? (
            <div className="mt-7 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {logos.map(
                (logo, index) => {
                  const selected =
                    logo.is_selected;

                  const selecting =
                    selectingLogo ===
                    logo.id;

                  const direction =
                    getDirection(index);

                  const palette =
                    cleanPalette(
                      logo.palette
                    );

                  return (
                    <article
                      key={logo.id}
                      className={`group overflow-hidden rounded-[22px] border bg-white/95 transition duration-300 ${
                        selected
                          ? "border-violet-400 shadow-[0_18px_50px_rgba(124,58,237,0.13)] ring-2 ring-violet-500/10"
                          : "border-white/90 shadow-[0_4px_20px_rgba(24,24,27,0.04)] hover:-translate-y-1 hover:border-zinc-200 hover:shadow-[0_22px_55px_rgba(24,24,27,0.08)]"
                      }`}
                    >
                      {/* Canvas */}

                      <div className="relative flex aspect-[4/3] items-center justify-center overflow-hidden bg-[#fafafa] p-8">
                        <div className="absolute inset-0 opacity-[0.028] [background-image:linear-gradient(#000_1px,transparent_1px),linear-gradient(90deg,#000_1px,transparent_1px)] [background-size:20px_20px]" />

                        <span className="absolute left-4 top-4 z-10 rounded-full border border-zinc-200 bg-white/90 px-2.5 py-1 text-[10px] font-semibold text-zinc-500 shadow-sm">
                          {String(
                            index + 1
                          ).padStart(
                            2,
                            "0"
                          )}
                        </span>

                        {selected && (
                          <span className="absolute right-4 top-4 z-10 rounded-full bg-violet-600 px-2.5 py-1 text-[10px] font-semibold text-white">
                            Ã¢Å“â€œ Selected
                          </span>
                        )}

                        <img
                          src={getAssetUrl(
                            logo.url
                          )}
                          alt={`${project.business_name} ${direction.name} logo`}
                          loading="lazy"
                          className="relative z-10 max-h-full max-w-full object-contain transition duration-300 group-hover:scale-[1.02]"
                        />
                      </div>

                      {/* Info */}

                      <div className="border-t border-zinc-100 p-5">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-sm font-semibold text-zinc-950">
                              {
                                direction.name
                              }
                            </p>

                            <p className="mt-1 max-w-[230px] text-xs leading-5 text-zinc-400">
                              {
                                direction.description
                              }
                            </p>
                          </div>

                          {palette && (
                            <div className="flex -space-x-1">
                              {[
                                palette.primary_color,
                                palette.secondary_color,
                                palette.accent_color,
                              ].map(
                                (
                                  color,
                                  colorIndex
                                ) => (
                                  <div
                                    key={`${color}-${colorIndex}`}
                                    title={
                                      color
                                    }
                                    className="h-6 w-6 rounded-full border-2 border-white shadow-sm"
                                    style={{
                                      backgroundColor:
                                        safeColor(
                                          color
                                        ),
                                    }}
                                  />
                                )
                              )}
                            </div>
                          )}
                        </div>

                        {palette && (
                          <div className="mt-4 grid grid-cols-3 gap-2">
                            {[
                              palette.primary_color,
                              palette.secondary_color,
                              palette.accent_color,
                            ].map(
                              (
                                color,
                                colorIndex
                              ) => (
                                <div
                                  key={`${color}-value-${colorIndex}`}
                                >
                                  <div
                                    className="h-1.5 rounded-full"
                                    style={{
                                      backgroundColor:
                                        safeColor(
                                          color
                                        ),
                                    }}
                                  />

                                  <p className="mt-1.5 truncate text-center font-mono text-[9px] uppercase text-zinc-400">
                                    {
                                      color
                                    }
                                  </p>
                                </div>
                              )
                            )}
                          </div>
                        )}

                        <button
                          type="button"
                          onClick={() =>
                            selectLogo(
                              logo.id
                            )
                          }
                          disabled={
                            selected ||
                            selectingLogo !==
                              null ||
                            generating
                          }
                          className={`mt-5 flex h-10 w-full items-center justify-center gap-2 rounded-xl text-sm font-semibold transition ${
                            selected
                              ? "bg-violet-50 text-violet-700"
                              : "bg-zinc-950 text-white hover:bg-zinc-800"
                          } disabled:cursor-not-allowed`}
                        >
                          {selecting && (
                            <span className="studio-spinner h-4 w-4 rounded-full border-2 border-white/30 border-t-white" />
                          )}

                          {selecting
                            ? "Building identity..."
                            : selected
                              ? "Ã¢Å“â€œ Selected direction"
                              : "Choose this direction"}
                        </button>
                      </div>
                    </article>
                  );
                }
              )}
            </div>
          ) : (
            <div className="mt-7 rounded-[22px] border border-dashed border-violet-200 bg-white/70 px-6 py-16 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-lg text-violet-600">
                Ã¢â€”â€¡
              </div>

              <h3 className="mt-5 text-base font-semibold text-zinc-900">
                No logo concepts yet
              </h3>

              <p className="mt-2 text-sm text-zinc-500">
                Generate your first three
                local AI logo directions.
              </p>

              <button
                type="button"
                onClick={generateMore}
                disabled={generating}
                className="mt-6 rounded-xl bg-zinc-950 px-5 py-2.5 text-sm font-semibold text-white"
              >
                Generate logo concepts
              </button>
            </div>
          )}

          {logos.length > 0 && (
            <div className="mt-7 text-center">
              <button
                type="button"
                onClick={generateMore}
                disabled={
                  generating ||
                  selectingLogo !== null
                }
                className="inline-flex h-10 items-center gap-2 rounded-xl border border-zinc-200 bg-white px-4 text-sm font-semibold text-zinc-600 shadow-sm transition hover:bg-zinc-50 disabled:opacity-50"
              >
                {generating ? (
                  <>
                    <span className="studio-spinner h-4 w-4 rounded-full border-2 border-zinc-200 border-t-violet-600" />
                    Developing concepts...
                  </>
                ) : (
                  <>
                    Explore more
                    directions
                  </>
                )}
              </button>
            </div>
          )}
        </section>

        {/* Selection instruction */}

        {!selectedLogo &&
          logos.length > 0 && (
            <section className="mb-10 rounded-[22px] border border-violet-100 bg-gradient-to-r from-violet-50/80 to-blue-50/60 p-6">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <p className="text-sm font-semibold text-zinc-900">
                    Ready to build your
                    brand system?
                  </p>

                  <p className="mt-1 text-sm leading-6 text-zinc-500">
                    Choose one direction to
                    finalize your palette,
                    messaging, typography and
                    promotional assets.
                  </p>
                </div>

                <span className="shrink-0 text-sm font-semibold text-violet-600">
                  Choose a concept 
                </span>
              </div>
            </section>
          )}

        {/* Selected brand */}

        {selectedLogo && (
          <section className="border-t border-zinc-200/80 py-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Brand identity
            </div>

            <h2 className="mt-4 text-3xl font-semibold tracking-[-0.035em] text-zinc-950">
              Your brand system
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
              Your selected direction has
              been developed into a complete
              identity system.
            </p>

            {/* Logo refinement */}

            <div className="mt-8 rounded-[24px] border border-violet-100 bg-gradient-to-br from-white to-violet-50/40 p-6 shadow-sm">
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">
                    Logo refinement
                  </p>

                  <h3 className="mt-2 text-xl font-semibold tracking-[-0.025em] text-zinc-950">
                    Refine without losing your approved identity
                  </h3>

                  <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
                    Adjust color, typography and composition. Your selected original stays untouched until you approve a revision.
                  </p>
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-3">
                {[
                  ["Primary", refinePrimary, setRefinePrimary],
                  ["Secondary", refineSecondary, setRefineSecondary],
                  ["Accent", refineAccent, setRefineAccent],
                ].map(([label, value, setter]) => (
                  <label
                    key={label as string}
                    className="block"
                  >
                    <span className="text-xs font-semibold text-zinc-600">
                      {label as string} color
                    </span>

                    <div className="mt-2 flex h-11 items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3">
                      <input
                        type="color"
                        value={
                          /^#[0-9A-Fa-f]{6}$/.test(value as string)
                            ? value as string
                            : "#171717"
                        }
                        onChange={(event) =>
                          (setter as (value: string) => void)(
                            event.target.value.toUpperCase()
                          )
                        }
                        className="h-7 w-8 cursor-pointer border-0 bg-transparent p-0"
                      />

                      <input
                        value={value as string}
                        onChange={(event) =>
                          (setter as (value: string) => void)(
                            event.target.value.toUpperCase()
                          )
                        }
                        placeholder="#171717"
                        maxLength={7}
                        className="min-w-0 flex-1 bg-transparent text-sm font-medium text-zinc-800 outline-none"
                      />
                    </div>
                  </label>
                ))}
              </div>

              <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <label className="block">
                  <span className="text-xs font-semibold text-zinc-600">
                    Typography
                  </span>
                  <select
                    value={refineTypography}
                    onChange={(event) =>
                      setRefineTypography(event.target.value)
                    }
                    className="mt-2 h-11 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-800 outline-none"
                  >
                    <option value="modern">Modern</option>
                    <option value="geometric">Geometric</option>
                    <option value="elegant">Elegant</option>
                    <option value="classic">Classic</option>
                    <option value="bold">Bold</option>
                  </select>
                </label>

                <label className="block">
                  <span className="text-xs font-semibold text-zinc-600">
                    Layout
                  </span>
                  <select
                    value={refineLayout}
                    onChange={(event) =>
                      setRefineLayout(event.target.value)
                    }
                    className="mt-2 h-11 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-800 outline-none"
                  >
                    <option value="horizontal">Horizontal</option>
                    <option value="stacked">Stacked</option>
                    <option value="emblem">Emblem</option>
                    <option value="typography-led">Typography led</option>
                  </select>
                </label>

                <label className="block">
                  <span className="text-xs font-semibold text-zinc-600">
                    Presentation
                  </span>
                  <select
                    value={refineBackground}
                    onChange={(event) =>
                      setRefineBackground(event.target.value)
                    }
                    className="mt-2 h-11 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-800 outline-none"
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                  </select>
                </label>

                <label className="block">
                  <span className="text-xs font-semibold text-zinc-600">
                    Treatment
                  </span>
                  <select
                    value={refineTreatment}
                    onChange={(event) =>
                      setRefineTreatment(event.target.value)
                    }
                    className="mt-2 h-11 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-800 outline-none"
                  >
                    <option value="premium-gradient">Premium</option>
                    <option value="flat">Flat</option>
                  </select>
                </label>
              </div>

              <label className="mt-4 block">
                <span className="text-xs font-semibold text-zinc-600">
                  Refinement note
                </span>

                <textarea
                  value={refineInstruction}
                  onChange={(event) =>
                    setRefineInstruction(event.target.value)
                  }
                  maxLength={500}
                  rows={3}
                  placeholder="Example: Make the identity more refined and editorial while preserving the core symbol."
                  className="mt-2 w-full resize-none rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm leading-6 text-zinc-800 outline-none placeholder:text-zinc-400"
                />
              </label>

              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={refineSelectedLogo}
                  disabled={
                    refiningLogo ||
                    selectingLogo !== null ||
                    generating
                  }
                  className="inline-flex h-11 items-center gap-2 rounded-xl bg-zinc-950 px-5 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {refiningLogo && (
                    <span className="studio-spinner h-4 w-4 rounded-full border-2 border-white/30 border-t-white" />
                  )}

                  {refiningLogo
                    ? "Creating revision..."
                    : "Create refinement"}
                </button>

                <span className="text-xs text-zinc-400">
                  Original logo remains unchanged.
                </span>
              </div>

              {latestRefinement && (
                <div className="mt-6 grid gap-5 border-t border-violet-100 pt-6 md:grid-cols-2">
                  <div className="rounded-2xl border border-zinc-200 bg-white p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-zinc-400">
                      Current selected
                    </p>
                    <div className="mt-3 flex min-h-[220px] items-center justify-center rounded-xl bg-zinc-50 p-6">
                      <img
                        src={getAssetUrl(selectedLogo.url)}
                        alt="Current selected logo"
                        className="max-h-[180px] max-w-full object-contain"
                      />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-violet-200 bg-white p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-violet-600">
                      New revision
                    </p>
                    <div className="mt-3 flex min-h-[220px] items-center justify-center rounded-xl bg-zinc-50 p-6">
                      <img
                        src={getAssetUrl(latestRefinement.url)}
                        alt="Refined logo revision"
                        className="max-h-[180px] max-w-full object-contain"
                      />
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        selectLogo(latestRefinement.id)
                      }
                      disabled={
                        selectingLogo !== null ||
                        refiningLogo
                      }
                      className="mt-4 h-10 w-full rounded-xl bg-violet-600 px-4 text-sm font-semibold text-white transition hover:bg-violet-700 disabled:opacity-50"
                    >
                      {selectingLogo === latestRefinement.id
                        ? "Selecting revision..."
                        : "Approve this revision"}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Logo + palette */}

            <div className="mt-8 grid gap-5 lg:grid-cols-[1.15fr_.85fr]">
              <StudioCard
                title="Primary logo"
                badge="Selected"
              >
                <div className="flex min-h-[330px] items-center justify-center bg-[#fafafa] p-10">
                  <img
                    src={getAssetUrl(
                      selectedLogo.url
                    )}
                    alt={`${project.business_name} selected logo`}
                    className="max-h-[240px] max-w-full object-contain"
                  />
                </div>

                <div className="flex items-center justify-between border-t border-zinc-100 px-5 py-4">
                  <p className="text-xs text-zinc-400">
                    Primary identity asset
                  </p>

                  <a
                    href={getAssetUrl(
                      selectedLogo.url
                    )}
                    download
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-lg border border-zinc-200 px-3 py-2 text-xs font-semibold text-zinc-700 transition hover:bg-zinc-50"
                  >
                     Download PNG
                  </a>
                </div>
              </StudioCard>

              <StudioCard title="Color palette">
                {displayedBrandPalette ? (
                  <div className="space-y-3 p-5">
                    <ColorCard
                      label="Primary"
                      color={
                        displayedBrandPalette.primary_color
                      }
                    />

                    <ColorCard
                      label="Secondary"
                      color={
                        displayedBrandPalette.secondary_color
                      }
                    />

                    <ColorCard
                      label="Accent"
                      color={
                        displayedBrandPalette.accent_color
                      }
                    />

                    <p className="pt-2 text-xs leading-5 text-zinc-400">
                      Click a color to copy
                      its HEX value.
                    </p>
                  </div>
                ) : (
                  <div className="flex min-h-[300px] items-center justify-center">
                    <p className="text-sm text-zinc-400">
                      Preparing brand
                      colors...
                    </p>
                  </div>
                )}
              </StudioCard>
            </div>

            {/* Intelligence */}

            {brandKit && (
              <>
                <div className="mt-10">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">
                    Brand intelligence
                  </p>

                  <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-950">
                    Strategy & personality
                  </h2>
                </div>

                <div className="mt-5 grid gap-5 lg:grid-cols-2">
                  <StrategyCard title="Brand personality">
                    {brandKit.personality
                      ?.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {brandKit.personality.map(
                          (
                            trait,
                            index
                          ) => (
                            <span
                              key={`${trait}-${index}`}
                              className="rounded-full border border-violet-100 bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700"
                            >
                              {
                                trait
                              }
                            </span>
                          )
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-zinc-500">
                        Professional
                      </p>
                    )}
                  </StrategyCard>

                  <StrategyCard title="Tone of voice">
                    <p className="text-sm leading-7 text-zinc-600">
                      {brandKit.tone ||
                        "Professional and approachable"}
                    </p>
                  </StrategyCard>

                  <StrategyCard title="Target audience">
                    <p className="text-sm leading-7 text-zinc-600">
                      {brandKit.target_audience ||
                        "Target audience information will appear here."}
                    </p>
                  </StrategyCard>

                  <StrategyCard title="Typography">
                    <div className="grid gap-5 sm:grid-cols-2">
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                          Heading
                        </p>

                        <p className="mt-2 text-2xl font-semibold text-zinc-900">
                          {brandKit.heading_font ||
                            "Montserrat"}
                        </p>

                        <p className="mt-1 text-xs text-zinc-400">
                          Aa Bb Cc 123
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                          Body
                        </p>

                        <p className="mt-2 text-xl text-zinc-800">
                          {brandKit.body_font ||
                            "Inter"}
                        </p>

                        <p className="mt-1 text-xs text-zinc-400">
                          Aa Bb Cc 123
                        </p>
                      </div>
                    </div>
                  </StrategyCard>
                </div>

                                {/* Messaging */}

                <div className="relative mt-5 overflow-hidden rounded-[24px] bg-zinc-950 p-7 text-white shadow-xl sm:p-9">
                  <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-violet-600/20 blur-[80px]" />

                  <div className="relative">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-300">
                      Brand messaging
                    </p>

                    {brandKit.slogan && (
                      <h3 className="mt-5 max-w-4xl text-3xl font-semibold leading-tight tracking-[-0.035em] sm:text-4xl">
                        Ã¢â‚¬Å“{brandKit.slogan}Ã¢â‚¬Â
                      </h3>
                    )}

                    {brandKit.marketing_message && (
                      <p className="mt-5 max-w-3xl text-sm leading-7 text-zinc-400 sm:text-base">
                        {brandKit.marketing_message}
                      </p>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* AI Brand Score */}

            {brandKit && projectId && (
              <BrandScorePanel projectId={projectId} />
            )}

            {/* Video */}

            <div className="mt-10">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-fuchsia-600">
                Promotional content
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-950">
                Brand animation
              </h2>
            </div>

            <div className="mt-5 overflow-hidden rounded-[24px] border border-white/90 bg-white/90 shadow-[0_15px_45px_rgba(24,24,27,0.06)]">
              {selectingLogo && (
                <div className="flex min-h-[280px] items-center justify-center bg-zinc-950 p-8 text-center">
                  <div>
                    <div className="studio-spinner mx-auto h-8 w-8 rounded-full border-[3px] border-zinc-700 border-t-fuchsia-400" />

                    <p className="mt-4 text-sm font-semibold text-white">
                      Creating brand animation...
                    </p>
                  </div>
                </div>
              )}

              {!selectingLogo && latestVideo && (
                <>
                  <div className="bg-zinc-950 p-4 sm:p-7">
                    <video
                      key={latestVideo.url}
                      muted
                      loop
                      controls
                      playsInline
                      preload="metadata"
                      className="mx-auto max-h-[620px] w-full rounded-xl bg-black object-contain"
                    >
                      <source
                        src={getAssetUrl(latestVideo.url)}
                        type="video/mp4"
                      />

                      Your browser does not support video playback.
                    </video>
                  </div>

                  <div className="flex flex-col justify-between gap-3 border-t border-zinc-100 px-5 py-4 sm:flex-row sm:items-center">
                    <div>
                      <p className="text-sm font-semibold text-zinc-800">
                        Promotional brand video
                      </p>

                      <p className="mt-0.5 text-xs text-zinc-400">
                        MP4 Ã‚Â· Generated from selected identity
                      </p>
                    </div>

                    <a
                      href={getAssetUrl(latestVideo.url)}
                      download
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-xl bg-zinc-950 px-4 py-2.5 text-center text-xs font-semibold text-white"
                    >
                       Download video
                    </a>
                  </div>
                </>
              )}

              {!selectingLogo && !latestVideo && (
                <div className="flex min-h-[260px] items-center justify-center p-8 text-center">
                  <div>
                    <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-fuchsia-50 text-fuchsia-600">
                      Ã¢â€“Â¶
                    </div>

                    <p className="mt-4 text-sm font-semibold text-zinc-800">
                      Video not available
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Package */}

            {brandKit && (
              <div className="relative mt-8 overflow-hidden rounded-[24px] border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-violet-50 p-7 sm:p-8">
                <div className="flex flex-col justify-between gap-7 lg:flex-row lg:items-center">
                  <div>
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                      
                    </div>

                    <h2 className="mt-4 text-xl font-semibold tracking-tight text-zinc-950">
                      Your complete brand
                      package
                    </h2>

                    <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
                      Download your logo,
                      promotional video,
                      guidelines and
                      structured brand data.
                    </p>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <PackageBadge text="PNG Logo" />

                      <PackageBadge text="MP4 Video" />

                      <PackageBadge text="PDF Guidelines" />

                      <PackageBadge text="JSON Data" />
                    </div>
                  </div>

                  <a
                    href={`${API}/projects/${projectId}/download-package`}
                    className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-zinc-950 px-5 text-sm font-semibold text-white transition hover:bg-zinc-800"
                  >
                     Download brand kit
                  </a>
                </div>
              </div>
            )}
          </section>
        )}

        {/* Summary */}

        <section className="grid gap-3 border-t border-zinc-200/80 py-8 sm:grid-cols-3">
          <SummaryCard
            title="Logo concepts"
            value={logos.length}
          />

          <SummaryCard
            title="Brand identity"
            value={
              selectedLogo
                ? "Selected Ã¢Å“â€œ"
                : "Awaiting selection"
            }
          />

          <SummaryCard
            title="Videos"
            value={videos.length}
          />
        </section>
      </div>

      {/* Footer */}

      <footer className="relative z-10 border-t border-white/80 bg-white/50 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 text-xs text-zinc-400 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-zinc-950 text-[9px] font-bold text-white">
              B
            </div>

            <span>
              BrandAI Studio
            </span>
          </div>

          <span>
            {project.business_name}
          </span>
        </div>
      </footer>
    </main>
  );
}

// ======================================================
// COMPONENTS
// ======================================================

function StudioCard({
  title,
  badge,
  children,
}: {
  title: string;
  badge?: string;
  children: ReactNode;
}) {
  return (
    <article className="overflow-hidden rounded-[22px] border border-white/90 bg-white/95 shadow-[0_10px_35px_rgba(24,24,27,0.05)]">
      <div className="flex items-center justify-between border-b border-zinc-100 px-5 py-4">
        <h3 className="text-sm font-semibold text-zinc-900">
          {title}
        </h3>

        {badge && (
          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold text-emerald-700">
            Ã¢Å“â€œ {badge}
          </span>
        )}
      </div>

      {children}
    </article>
  );
}

function StrategyCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <article className="rounded-[20px] border border-white/90 bg-white/90 p-6 shadow-[0_8px_30px_rgba(24,24,27,0.04)]">
      <p className="mb-4 text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-400">
        {title}
      </p>

      {children}
    </article>
  );
}

function ColorCard({
  label,
  color,
}: {
  label: string;
  color: string;
}) {
  const [copied, setCopied] =
    useState(false);

  async function copyColor() {
    try {
      await navigator.clipboard.writeText(
        color
      );

      setCopied(true);

      window.setTimeout(
        () => setCopied(false),
        1200
      );
    } catch {
      // Clipboard may be unavailable.
    }
  }

  return (
    <button
      type="button"
      onClick={copyColor}
      className="group flex w-full items-center gap-4 rounded-xl border border-zinc-100 bg-white p-3 text-left transition hover:border-zinc-200 hover:bg-zinc-50"
      title={`Copy ${color}`}
    >
      <div
        className="h-12 w-12 shrink-0 rounded-xl border border-black/5 shadow-sm"
        style={{
          backgroundColor:
            safeColor(color),
        }}
      />

      <div className="min-w-0">
        <p className="text-[11px] font-medium text-zinc-400">
          {label}
        </p>

        <p className="mt-1 font-mono text-sm font-semibold uppercase text-zinc-800">
          {color}
        </p>
      </div>

      <span className="ml-auto text-[11px] font-medium text-zinc-400 transition group-hover:text-violet-600">
        {copied ? "Copied Ã¢Å“â€œ" : "Copy"}
      </span>
    </button>
  );
}

function PackageBadge({
  text,
}: {
  text: string;
}) {
  return (
    <span className="rounded-lg border border-white bg-white/80 px-2.5 py-1.5 text-[10px] font-medium text-zinc-500 shadow-sm">
      {text}
    </span>
  );
}

function SummaryCard({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) {
  return (
    <div className="rounded-xl border border-white/90 bg-white/60 px-4 py-3.5 backdrop-blur">
      <p className="text-[11px] text-zinc-400">
        {title}
      </p>

      <p className="mt-1 text-sm font-semibold text-zinc-800">
        {value}
      </p>
    </div>
  );
}
