"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { useParams } from "next/navigation";
import Link from "next/link";


const API = "http://127.0.0.1:8000";


interface Project {
  id: string;
  business_name: string;
  description: string;
  industry: string;
  style: string;
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
  created_at: string;
}


export default function ProjectPage() {

  const params = useParams();

  const projectId =
    params.id as string;


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

  const [
    selectingLogo,
    setSelectingLogo,
  ] = useState<string | null>(null);

  const [error, setError] =
    useState("");


  // ======================================================
  // LOAD DATA
  // ======================================================

  const loadData =
    useCallback(
      async () => {

        try {

          setError("");


          const [
            projectResponse,
            assetsResponse,
            brandKitResponse,
          ] =
            await Promise.all([

              fetch(
                `${API}/projects/${projectId}`
              ),

              fetch(
                `${API}/projects/${projectId}/assets`
              ),

              fetch(
                `${API}/projects/${projectId}/brand-kit`
              ),

            ]);


          if (!projectResponse.ok) {
            throw new Error(
              "Could not load project."
            );
          }


          if (!assetsResponse.ok) {
            throw new Error(
              "Could not load assets."
            );
          }


          if (!brandKitResponse.ok) {
            throw new Error(
              "Could not load brand kit."
            );
          }


          const projectData =
            await projectResponse.json();

          const assetsData =
            await assetsResponse.json();

          const brandKitData =
            await brandKitResponse.json();


          setProject(
            projectData.project
          );


          setAssets(
            assetsData.assets
          );


          setBrandKit(
            brandKitData.brand_kit
          );


        } catch (error) {

          console.error(error);


          setError(
            error instanceof Error
              ? error.message
              : "Could not load project."
          );


        } finally {

          setLoading(false);

        }

      },
      [projectId]
    );


  useEffect(() => {

    if (projectId) {
      loadData();
    }

  }, [projectId, loadData]);


  // ======================================================
  // GENERATE 3 MORE
  // ======================================================

  async function generateMore() {

    try {

      setGenerating(true);

      setError("");


      const response =
        await fetch(
          `${API}/projects/${projectId}/generate-logo`,
          {
            method: "POST",
          }
        );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Could not generate concepts."
        );

      }


      setAssets(
        (previous) => [
          ...data.concepts,
          ...previous,
        ]
      );


    } catch (error) {

      console.error(error);


      setError(
        error instanceof Error
          ? error.message
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

    try {

      setSelectingLogo(
        logoId
      );

      setError("");


      const response =
        await fetch(
          `${API}/projects/${projectId}/logos/${logoId}/select`,
          {
            method: "POST",
          }
        );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Could not select logo."
        );

      }


      setAssets(
        (previous) => {

          const updated =
            previous.map(
              (asset) => ({

                ...asset,

                is_selected:
                  asset.asset_type === "logo"
                    ? asset.id === logoId
                    : asset.is_selected,

              })
            );


          return [
            data.video,
            ...updated,
          ];

        }
      );


      setBrandKit(
        data.brand_kit
      );


    } catch (error) {

      console.error(error);


      setError(
        error instanceof Error
          ? error.message
          : "Could not select logo."
      );


    } finally {

      setSelectingLogo(
        null
      );

    }

  }


  // ======================================================
  // FILTER ASSETS
  // ======================================================

  const logos =
    assets.filter(
      (asset) =>
        asset.asset_type === "logo"
    );


  const videos =
    assets.filter(
      (asset) =>
        asset.asset_type === "video"
    );


  // Only show newest three concepts.
  const visibleLogos =
    logos.slice(0, 3);


  const selectedLogo =
    logos.find(
      (logo) =>
        logo.is_selected
    ) ?? null;


  const latestVideo =
    videos.length > 0
      ? videos[0]
      : null;


  // ======================================================
  // LOADING
  // ======================================================

  if (loading) {

    return (

      <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">

        <div className="text-center">

          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-slate-700 border-t-violet-500" />


          <p className="mt-4 text-sm text-slate-400">
            Preparing your brand...
          </p>

        </div>

      </main>

    );

  }


  // ======================================================
  // PROJECT NOT FOUND
  // ======================================================

  if (!project) {

    return (

      <main className="flex min-h-screen flex-col items-center justify-center bg-slate-950 text-white">

        <p className="text-red-400">
          Project not found.
        </p>


        <Link
          href="/dashboard"
          className="mt-5 text-violet-400"
        >
          Back to Dashboard
        </Link>

      </main>

    );

  }


  // ======================================================
  // PAGE
  // ======================================================

  return (

    <main className="min-h-screen bg-slate-950 text-white">


      {/* ================================================
          NAVIGATION
      ================================================ */}

      <nav className="border-b border-slate-800">

        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">

          <Link
            href="/"
            className="text-xl font-bold text-violet-400"
          >
            BrandAI
          </Link>


          <Link
            href="/dashboard"
            className="text-sm text-slate-400 transition hover:text-white"
          >
            ← Dashboard
          </Link>

        </div>

      </nav>


      {/* ================================================
          CONTENT
      ================================================ */}

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6">


        {/* ================================================
            PROJECT HEADER
        ================================================ */}

        <div className="mb-8">

          <span className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-400">
            {project.industry}
          </span>


          <h1 className="mt-4 text-3xl font-bold sm:text-4xl">
            {project.business_name}
          </h1>


          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400 sm:text-base">
            {project.description}
          </p>


          <p className="mt-3 text-sm text-slate-500">

            Brand style:{" "}

            <span className="font-medium text-slate-300">
              {project.style}
            </span>

          </p>

        </div>


        {/* ================================================
            ERROR
        ================================================ */}

        {error && (

          <div className="mb-6 rounded-xl border border-red-800 bg-red-950/40 p-4 text-sm text-red-300">
            {error}
          </div>

        )}


        {/* ================================================
            LOGO CONCEPTS
        ================================================ */}

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">


          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">


            <div>

              <p className="text-xs font-bold tracking-wide text-violet-400">
                BRAND CONCEPTS
              </p>


              <h2 className="mt-1 text-xl font-bold sm:text-2xl">
                Choose Your Identity
              </h2>


              <p className="mt-2 text-sm text-slate-400">
                Select one logo to automatically
                complete your brand kit and video.
              </p>

            </div>


            <button
              type="button"
              onClick={generateMore}
              disabled={generating}
              className="shrink-0 rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-semibold transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
            >

              {generating
                ? "Generating..."
                : "Generate 3 More"}

            </button>

          </div>


          {/* LOGO GRID */}

          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">


            {visibleLogos.map(
              (logo, index) => (

                <article
                  key={logo.id}
                  className={`overflow-hidden rounded-xl border transition ${
                    logo.is_selected
                      ? "border-emerald-400 bg-emerald-500/5"
                      : "border-slate-700 bg-slate-950"
                  }`}
                >


                  {/* IMAGE */}

                  <div className="relative flex h-52 items-center justify-center bg-white p-4 sm:h-56">


                    <img
                      src={logo.url}
                      alt={`Logo concept ${index + 1}`}
                      className="h-full w-full object-contain"
                    />


                    {logo.is_selected && (

                      <span className="absolute right-2 top-2 rounded-full bg-emerald-500 px-2.5 py-1 text-[10px] font-bold text-white">
                        ✓ SELECTED
                      </span>

                    )}

                  </div>


                  {/* CARD CONTENT */}

                  <div className="p-4">


                    <p className="text-sm font-semibold text-slate-300">
                      Concept {index + 1}
                    </p>


                    {/* PALETTE */}

                    {logo.palette && (

                      <div className="mt-3">


                        <p className="mb-2 text-[10px] font-semibold tracking-wider text-slate-500">
                          COLOR PALETTE
                        </p>


                        <div className="grid grid-cols-3 gap-2">


                          {[
                            logo.palette.primary_color,
                            logo.palette.secondary_color,
                            logo.palette.accent_color,
                          ].map(
                            (
                              color,
                              colorIndex
                            ) => (

                              <div
                                key={`${color}-${colorIndex}`}
                              >


                                <div
                                  className="h-7 rounded-md border border-white/10"
                                  style={{
                                    backgroundColor:
                                      color,
                                  }}
                                />


                                <p className="mt-1 text-center font-mono text-[10px] text-slate-500">
                                  {color}
                                </p>

                              </div>

                            )
                          )}

                        </div>

                      </div>

                    )}


                    {/* SELECT */}

                    <button
                      type="button"
                      onClick={() =>
                        selectLogo(
                          logo.id
                        )
                      }
                      disabled={
                        logo.is_selected ||
                        selectingLogo !== null
                      }
                      className={`mt-4 w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
                        logo.is_selected
                          ? "bg-emerald-500/15 text-emerald-300"
                          : "bg-violet-600 hover:bg-violet-500"
                      } disabled:cursor-not-allowed`}
                    >

                      {logo.is_selected
                        ? "✓ Selected"
                        : selectingLogo === logo.id
                          ? "Preparing Brand..."
                          : "Choose Logo"}

                    </button>

                  </div>

                </article>

              )
            )}

          </div>


          {visibleLogos.length === 0 && (

            <div className="mt-6 flex h-44 items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-950">

              <p className="text-sm text-slate-500">
                No logo concepts available.
              </p>

            </div>

          )}

        </section>


        {/* ================================================
            SELECTED BRAND
        ================================================ */}

        {selectedLogo && (

          <section className="mt-6">


            <div className="mb-4">

              <p className="text-xs font-bold tracking-wide text-emerald-400">
                FINAL BRAND IDENTITY
              </p>


              <h2 className="mt-1 text-2xl font-bold">
                Your Brand
              </h2>

            </div>


            <div className="grid gap-4 md:grid-cols-2">


              {/* SELECTED LOGO */}

              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">


                <div className="flex items-center justify-between">

                  <h3 className="font-semibold">
                    Selected Logo
                  </h3>


                  <span className="rounded-full bg-emerald-500/10 px-2 py-1 text-[10px] font-bold text-emerald-400">
                    READY
                  </span>

                </div>


                <div className="mt-4 flex h-64 items-center justify-center rounded-xl bg-white p-4">

                  <img
                    src={selectedLogo.url}
                    alt={`${project.business_name} logo`}
                    className="h-full w-full object-contain"
                  />

                </div>


                <a
                  href={selectedLogo.url}
                  download
                  className="mt-4 block rounded-lg border border-slate-700 py-2.5 text-center text-sm font-semibold transition hover:border-violet-500 hover:text-violet-300"
                >
                  Download Logo
                </a>

              </div>


              {/* BRAND PALETTE */}

              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">


                <h3 className="font-semibold">
                  Brand Color Palette
                </h3>


                <p className="mt-1 text-xs text-slate-500">
                  Extracted automatically from
                  your selected logo.
                </p>


                {brandKit ? (

                  <div className="mt-4 space-y-3">

                    <ColorCard
                      label="Primary"
                      color={
                        brandKit.primary_color
                      }
                    />


                    <ColorCard
                      label="Secondary"
                      color={
                        brandKit.secondary_color
                      }
                    />


                    <ColorCard
                      label="Accent"
                      color={
                        brandKit.accent_color
                      }
                    />

                  </div>

                ) : (

                  <div className="mt-4 flex h-48 items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-950">

                    <p className="text-sm text-slate-500">
                      Preparing palette...
                    </p>

                  </div>

                )}

              </div>

            </div>

          </section>

        )}


        {/* ================================================
            VIDEO
        ================================================ */}

        {selectedLogo && (

          <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">


            <p className="text-xs font-bold tracking-wide text-fuchsia-400">
              PROMOTIONAL VIDEO
            </p>


            <h2 className="mt-1 text-xl font-bold">
              Brand Animation
            </h2>


            <p className="mt-2 text-sm text-slate-400">
              Automatically created from
              your selected brand identity.
            </p>


            {selectingLogo && (

              <div className="mt-5 flex items-center gap-3 text-sm text-slate-400">

                <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-700 border-t-fuchsia-500" />

                Generating video...

              </div>

            )}


            {latestVideo ? (

              <div className="mt-5 max-w-xl">


                <video
                  key={latestVideo.url}
                  autoPlay
                  muted
                  loop
                  controls
                  playsInline
                  className="max-h-[420px] w-full rounded-xl border border-slate-800 bg-black object-contain"
                >

                  <source
                    src={latestVideo.url}
                    type="video/mp4"
                  />

                </video>


                <a
                  href={latestVideo.url}
                  download
                  className="mt-3 block rounded-lg bg-fuchsia-600 py-2.5 text-center text-sm font-semibold transition hover:bg-fuchsia-500"
                >
                  Download Video
                </a>

              </div>

            ) : (

              !selectingLogo && (

                <div className="mt-5 flex h-48 max-w-xl items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-950">

                  <p className="text-sm text-slate-500">
                    Video is being prepared.
                  </p>

                </div>

              )

            )}

          </section>

        )}


        {/* ================================================
            SMALL SUMMARY
        ================================================ */}

        <section className="mt-6 grid gap-3 sm:grid-cols-3">


          <SummaryCard
            title="Logo Concepts"
            value={logos.length}
          />


          <SummaryCard
            title="Brand Identity"
            value={
              selectedLogo
                ? "Selected ✓"
                : "Choose logo"
            }
          />


          <SummaryCard
            title="Videos"
            value={videos.length}
          />


        </section>


      </section>

    </main>

  );

}


// ======================================================
// COLOR CARD
// ======================================================

function ColorCard({
  label,
  color,
}: {
  label: string;
  color: string;
}) {

  return (

    <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 p-3">


      <div
        className="h-11 w-11 shrink-0 rounded-md border border-white/10"
        style={{
          backgroundColor: color,
        }}
      />


      <div>

        <p className="text-xs text-slate-500">
          {label}
        </p>


        <p className="mt-0.5 font-mono text-sm font-semibold">
          {color}
        </p>

      </div>

    </div>

  );

}


// ======================================================
// SUMMARY CARD
// ======================================================

function SummaryCard({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) {

  return (

    <div className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-3">


      <p className="text-xs text-slate-500">
        {title}
      </p>


      <p className="mt-1 font-semibold">
        {value}
      </p>


    </div>

  );

}