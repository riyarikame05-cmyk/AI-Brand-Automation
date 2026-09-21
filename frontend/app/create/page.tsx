"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const INDUSTRIES = [
  { value: "clothing", label: "Clothing & Fashion" },
  { value: "textile", label: "Textile" },
  { value: "technology", label: "Technology / Software" },
  { value: "ai", label: "Artificial Intelligence" },
  { value: "ecommerce", label: "E-commerce" },
  { value: "restaurant", label: "Food & Restaurant" },
  { value: "coffee", label: "Coffee & Cafe" },
  { value: "healthcare", label: "Healthcare" },
  { value: "beauty", label: "Beauty & Cosmetics" },
  { value: "fitness", label: "Fitness & Gym" },
  { value: "education", label: "Education" },
  { value: "finance", label: "Finance & Banking" },
  { value: "realestate", label: "Real Estate" },
  { value: "automotive", label: "Automotive" },
  { value: "travel", label: "Travel & Tourism" },
  { value: "music", label: "Music & Entertainment" },
  { value: "gaming", label: "Gaming" },
  { value: "construction", label: "Construction" },
  { value: "agriculture", label: "Agriculture" },
  { value: "jewellery", label: "Jewellery" },
  { value: "photography", label: "Photography" },
  { value: "marketing", label: "Marketing & Advertising" },
  { value: "logistics", label: "Logistics & Transportation" },
];

const STYLES = [
  { value: "minimalist", label: "Minimal" },
  { value: "modern", label: "Modern" },
  { value: "luxury", label: "Luxury" },
  { value: "playful", label: "Playful" },
  { value: "futuristic", label: "Futuristic" },
  { value: "corporate", label: "Professional / Corporate" },
];

type CreationStage =
  | "idle"
  | "brand"
  | "logos"
  | "complete";

export default function CreateBrandPage() {
  const router = useRouter();

  const [businessName, setBusinessName] = useState("");
  const [description, setDescription] = useState("");
  const [industry, setIndustry] = useState("");
  const [style, setStyle] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [stage, setStage] = useState<CreationStage>("idle");
  const [error, setError] = useState("");

  async function readResponse(response: Response) {
    const text = await response.text();

    if (!text) {
      return {};
    }

    try {
      return JSON.parse(text);
    } catch {
      throw new Error(
        `Server returned an invalid response (${response.status}).`
      );
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (submitting) {
      return;
    }

    setSubmitting(true);
    setError("");
    setStage("brand");

    let projectId: number | string | null = null;

    try {
      /*
       * STEP 1
       * Create the project and brand strategy.
       *
       * Backend v6 does NOT generate logos here.
       */
      const brandResponse = await fetch(`${API_URL}/brand`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          business_name: businessName.trim(),
          description: description.trim(),
          industry,
          style,
        }),
      });

      const brandData = await readResponse(brandResponse);

      if (!brandResponse.ok) {
        throw new Error(
          brandData?.detail ||
            brandData?.message ||
            "Could not create brand project."
        );
      }

      projectId = brandData?.project?.id;

      if (!projectId) {
        throw new Error(
          "Brand project was created, but the server did not return a project ID."
        );
      }

      /*
       * STEP 2
       * Generate the three logo concepts.
       *
       * Backend controls the three creative directions:
       *
       * 0 - minimal-geometric
       * 1 - symbolic-negative-space
       * 2 - typographic
       */
      setStage("logos");

      const logoResponse = await fetch(
        `${API_URL}/projects/${projectId}/generate-logo`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const logoData = await readResponse(logoResponse);

      if (!logoResponse.ok) {
        throw new Error(
          logoData?.detail ||
            logoData?.message ||
            "Brand project was created, but logo generation failed."
        );
      }

      setStage("complete");

      /*
       * STEP 3
       * Open the project page.
       *
       * The user can now compare the three concepts and
       * select one. Video generation happens only after
       * logo selection.
       */
      router.push(`/projects/${projectId}`);
    } catch (caughtError) {
      console.error(caughtError);

      let message =
        caughtError instanceof Error
          ? caughtError.message
          : "Could not create brand.";

      /*
       * If the project itself succeeded but logo generation
       * failed, tell the user that their project still exists.
       */
      if (projectId) {
        message +=
          " Your project was saved. You can open it from the dashboard and retry logo generation.";
      }

      setError(message);
      setStage("idle");
      setSubmitting(false);
    }
  }

  function getButtonText() {
    if (!submitting) {
      return "Generate My Brand";
    }

    switch (stage) {
      case "brand":
        return "Creating Brand Strategy...";

      case "logos":
        return "Generating Logo Concepts...";

      case "complete":
        return "Opening Your Brand...";

      default:
        return "Creating Brand...";
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-slate-800 px-8 py-5">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Link
            href="/"
            className="text-2xl font-bold text-violet-400"
          >
            BrandAI
          </Link>

          <Link
            href="/dashboard"
            className="text-slate-400 transition hover:text-white"
          >
            Dashboard
          </Link>
        </div>
      </nav>

      <section className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm font-semibold text-violet-400">
          AI BRAND AUTOMATION
        </p>

        <h1 className="mt-2 text-4xl font-bold">
          Create Your Brand
        </h1>

        <p className="mt-3 text-slate-400">
          Enter your company information. BrandAI will build your
          brand strategy and generate three distinct logo concepts.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-10 space-y-6 rounded-2xl border border-slate-800 bg-slate-900 p-8"
        >
          <div>
            <label
              htmlFor="business-name"
              className="mb-2 block font-medium"
            >
              Business Name
            </label>

            <input
              id="business-name"
              value={businessName}
              onChange={(event) =>
                setBusinessName(event.target.value)
              }
              required
              disabled={submitting}
              placeholder="Example: Nova Technologies"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition focus:border-violet-500 disabled:opacity-60"
            />
          </div>

          <div>
            <label
              htmlFor="industry"
              className="mb-2 block font-medium"
            >
              Industry
            </label>

            <select
              id="industry"
              value={industry}
              onChange={(event) =>
                setIndustry(event.target.value)
              }
              required
              disabled={submitting}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition focus:border-violet-500 disabled:opacity-60"
            >
              <option value="">
                Select industry
              </option>

              {INDUSTRIES.map((item) => (
                <option
                  key={item.value}
                  value={item.value}
                >
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="description"
              className="mb-2 block font-medium"
            >
              Business Description
            </label>

            <textarea
              id="description"
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
              required
              rows={5}
              disabled={submitting}
              placeholder="Describe your company, products and customers..."
              className="w-full resize-none rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition focus:border-violet-500 disabled:opacity-60"
            />
          </div>

          <div>
            <label
              htmlFor="style"
              className="mb-2 block font-medium"
            >
              Brand Style
            </label>

            <select
              id="style"
              value={style}
              onChange={(event) =>
                setStyle(event.target.value)
              }
              required
              disabled={submitting}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition focus:border-violet-500 disabled:opacity-60"
            >
              <option value="">
                Select style
              </option>

              {STYLES.map((item) => (
                <option
                  key={item.value}
                  value={item.value}
                >
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="rounded-lg border border-red-800 bg-red-950/40 p-4 text-red-300">
              <p>{error}</p>

              <Link
                href="/dashboard"
                className="mt-2 inline-block font-medium text-red-200 underline hover:text-white"
              >
                Open Dashboard
              </Link>
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-violet-600 px-5 py-3 font-semibold transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {getButtonText()}
          </button>

          {submitting && (
            <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-950/60 p-4">
              <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                <div
                  className={`h-full rounded-full bg-violet-500 transition-all duration-500 ${
                    stage === "brand"
                      ? "w-1/3"
                      : stage === "logos"
                        ? "w-2/3"
                        : "w-full"
                  }`}
                />
              </div>

              <p className="text-center text-sm text-slate-400">
                {stage === "brand" &&
                  "Analysing your business and creating the brand strategy..."}

                {stage === "logos" &&
                  "Creating three distinct logo directions. Local AI generation can take a little time..."}

                {stage === "complete" &&
                  "Your brand concepts are ready. Opening the project..."}
              </p>
            </div>
          )}
        </form>
      </section>
    </main>
  );
}