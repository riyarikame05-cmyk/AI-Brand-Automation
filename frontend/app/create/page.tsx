"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

const INDUSTRIES = [
  "Technology / Software",
  "Artificial Intelligence",
  "Clothing & Fashion",
  "E-commerce",
  "Food & Restaurant",
  "Coffee & Cafe",
  "Healthcare",
  "Beauty & Cosmetics",
  "Fitness & Gym",
  "Education",
  "Finance & Banking",
  "Real Estate",
  "Automotive",
  "Travel & Tourism",
  "Music & Entertainment",
  "Gaming",
  "Construction",
  "Agriculture",
  "Jewellery",
  "Photography",
  "Marketing & Advertising",
  "Logistics & Transportation",
];

const LOGO_STYLES = [
  {
    id: "minimalist",
    name: "Minimal",
    description: "Simple and timeless",
    preview: "◇",
  },
  {
    id: "geometric",
    name: "Geometric",
    description: "Structured shapes",
    preview: "◆",
  },
  {
    id: "wordmark",
    name: "Wordmark",
    description: "Typography focused",
    preview: "Aa",
  },
  {
    id: "monogram",
    name: "Monogram",
    description: "Letter based mark",
    preview: "N",
  },
  {
    id: "luxury",
    name: "Luxury",
    description: "Elegant and premium",
    preview: "✦",
  },
  {
    id: "playful",
    name: "Playful",
    description: "Friendly and expressive",
    preview: "●",
  },
  {
    id: "futuristic",
    name: "Futuristic",
    description: "Modern and innovative",
    preview: "⬡",
  },
  {
    id: "corporate",
    name: "Corporate",
    description: "Trusted and professional",
    preview: "■",
  },
];

const PALETTES = [
  {
    id: "professional",
    name: "Professional",
    colors: ["#18181B", "#475569", "#E2E8F0"],
  },
  {
    id: "technology",
    name: "Technology",
    colors: ["#18181B", "#6D5DFC", "#DDD6FE"],
  },
  {
    id: "luxury",
    name: "Luxury",
    colors: ["#171717", "#B68D40", "#F5ECD7"],
  },
  {
    id: "nature",
    name: "Nature",
    colors: ["#14532D", "#22C55E", "#DCFCE7"],
  },
  {
    id: "energetic",
    name: "Energetic",
    colors: ["#BE123C", "#FB7185", "#FFF1F2"],
  },
  {
    id: "ocean",
    name: "Ocean",
    colors: ["#0C4A6E", "#0EA5E9", "#E0F2FE"],
  },
  {
    id: "warm",
    name: "Warm",
    colors: ["#7C2D12", "#F97316", "#FFEDD5"],
  },
  {
    id: "monochrome",
    name: "Monochrome",
    colors: ["#09090B", "#71717A", "#F4F4F5"],
  },
];

type Stage = "idle" | "brand" | "logos" | "complete";

export default function CreateBrandPage() {
  const router = useRouter();

  const [businessName, setBusinessName] = useState("");
  const [industry, setIndustry] = useState("");
  const [description, setDescription] = useState("");

  const [conceptCount, setConceptCount] = useState(3);
  const [logoStyle, setLogoStyle] = useState("minimalist");
  const [palette, setPalette] = useState("technology");

  const [customColors, setCustomColors] = useState([
    "#6D5DFC",
    "#18181B",
    "#DDD6FE",
  ]);

  const [useCustomColors, setUseCustomColors] = useState(false);
  const [creativeDirection, setCreativeDirection] = useState("");

  const [stage, setStage] = useState<Stage>("idle");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const selectedPalette = PALETTES.find(
    (item) => item.id === palette
  );

  async function readResponse(response: Response) {
    const text = await response.text();

    if (!text) return {};

    try {
      return JSON.parse(text);
    } catch {
      throw new Error(
        `Server returned an invalid response (${response.status}).`
      );
    }
  }

  function buildEnhancedDescription() {
    const colors = useCustomColors
      ? customColors.join(", ")
      : selectedPalette?.colors.join(", ");

    const extras = [
      description.trim(),
      `Preferred logo direction: ${logoStyle}.`,
      `Preferred color palette: ${colors}.`,
      creativeDirection.trim()
        ? `Additional creative direction: ${creativeDirection.trim()}`
        : "",
    ];

    return extras.filter(Boolean).join("\n\n");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (submitting) return;

    if (!businessName.trim()) {
      setError("Enter your business name.");
      return;
    }

    if (!industry) {
      setError("Choose an industry.");
      return;
    }

    if (!description.trim()) {
      setError("Tell us a little about your business.");
      return;
    }

    let projectId: string | number | null = null;

    try {
      setSubmitting(true);
      setError("");
      setStage("brand");

      const brandResponse = await fetch(`${API}/brand`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          business_name: businessName.trim(),
          industry,
          description: buildEnhancedDescription(),
          style: logoStyle,
        }),
      });

      const brandData = await readResponse(brandResponse);

      if (!brandResponse.ok) {
        throw new Error(
          brandData?.detail ||
            brandData?.message ||
            "Could not create brand."
        );
      }

      projectId = brandData?.project?.id;

      if (!projectId) {
        throw new Error("Server did not return a project ID.");
      }

      setStage("logos");

      /*
       * Current backend generates a three-concept batch.
       * For 6/9, request additional batches.
       */
      const batches = Math.max(1, conceptCount / 3);

      for (let batch = 0; batch < batches; batch += 1) {
        const logoResponse = await fetch(
          `${API}/projects/${projectId}/generate-logo`,
          {
            method: "POST",
            headers: {
              Accept: "application/json",
            },
          }
        );

        const logoData = await readResponse(logoResponse);

        if (!logoResponse.ok) {
          throw new Error(
            logoData?.detail ||
              logoData?.message ||
              "Logo generation failed."
          );
        }
      }

      setStage("complete");

      router.push(`/projects/${projectId}`);
    } catch (caughtError) {
      console.error(caughtError);

      let message =
        caughtError instanceof Error
          ? caughtError.message
          : "Could not create your brand.";

      if (projectId) {
        message += " Your project was saved.";
      }

      setError(message);
      setStage("idle");
      setSubmitting(false);
    }
  }

  const progress =
    stage === "brand"
      ? 25
      : stage === "logos"
        ? 70
        : stage === "complete"
          ? 100
          : 0;

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f7f7fb] text-zinc-900">
      {/* Background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
      >
        <div className="absolute -left-48 top-24 h-[600px] w-[600px] rounded-full bg-violet-300/20 blur-[140px]" />
        <div className="absolute -right-48 top-[500px] h-[650px] w-[650px] rounded-full bg-blue-200/25 blur-[150px]" />
        <div className="absolute bottom-0 left-1/3 h-[500px] w-[600px] rounded-full bg-fuchsia-200/15 blur-[150px]" />
      </div>

      {/* Header */}
      <header className="relative z-30 border-b border-white/70 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-950 text-sm font-bold text-white">
              B
            </div>

            <span className="text-[15px] font-semibold">
              BrandAI
            </span>
          </Link>

          <div className="flex items-center gap-2">
            <Link
              href="/dashboard"
              className="rounded-lg px-3 py-2 text-sm font-medium text-zinc-500 transition hover:bg-white hover:text-zinc-900"
            >
              Dashboard
            </Link>

            <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1.5 text-[11px] font-semibold text-violet-700">
              Local AI
            </span>
          </div>
        </div>
      </header>

      {/* Intro */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-8 pt-12 lg:px-8">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white/70 px-3 py-1.5 text-xs font-semibold text-violet-700 shadow-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-500" />
            AI Logo Builder
          </div>

          <h1 className="mt-5 text-4xl font-semibold tracking-[-0.045em] text-zinc-950 sm:text-5xl">
            Design your brand,
            <span className="text-violet-600"> your way.</span>
          </h1>

          <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-500">
            Give the local AI a creative brief, choose your visual
            direction and generate a complete brand identity.
          </p>
        </div>
      </section>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="relative z-10 mx-auto max-w-7xl px-6 pb-20 lg:px-8"
      >
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          {/* Main */}
          <div className="space-y-6">
            {/* Section 1 */}
            <FormSection
              number="01"
              title="Tell us about your business"
              description="Start with the basics so AI understands your brand."
            >
              <div className="grid gap-5 sm:grid-cols-2">
                <Field label="Business name">
                  <input
                    value={businessName}
                    onChange={(event) =>
                      setBusinessName(event.target.value)
                    }
                    disabled={submitting}
                    placeholder="e.g. Nova Technologies"
                    className={inputClass}
                  />
                </Field>

                <Field label="Industry">
                  <select
                    value={industry}
                    onChange={(event) =>
                      setIndustry(event.target.value)
                    }
                    disabled={submitting}
                    className={inputClass}
                  >
                    <option value="">Choose industry</option>

                    {INDUSTRIES.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="mt-5">
                <Field
                  label="Business description"
                  hint={`${description.length} characters`}
                >
                  <textarea
                    value={description}
                    onChange={(event) =>
                      setDescription(event.target.value)
                    }
                    disabled={submitting}
                    rows={4}
                    placeholder="What does your business do, who is it for, and what makes it different?"
                    className={`${inputClass} h-auto resize-none py-3.5`}
                  />
                </Field>
              </div>
            </FormSection>

            {/* Section 2 */}
            <FormSection
              number="02"
              title="Choose your logo direction"
              description="Control how your logo should feel and how many ideas to explore."
            >
              <p className="text-sm font-semibold text-zinc-800">
                Number of concepts
              </p>

              <div className="mt-3 grid grid-cols-3 gap-3">
                {[3, 6, 9].map((count) => {
                  const selected = conceptCount === count;

                  return (
                    <button
                      key={count}
                      type="button"
                      disabled={submitting}
                      onClick={() => setConceptCount(count)}
                      className={`rounded-xl border p-4 text-center transition ${
                        selected
                          ? "border-violet-500 bg-violet-50 ring-1 ring-violet-500"
                          : "border-zinc-200 bg-white hover:border-zinc-300"
                      }`}
                    >
                      <span className="block text-xl font-semibold text-zinc-900">
                        {count}
                      </span>

                      <span className="mt-1 block text-[11px] text-zinc-400">
                        concepts
                      </span>
                    </button>
                  );
                })}
              </div>

              <div className="mt-7">
                <p className="text-sm font-semibold text-zinc-800">
                  Logo style
                </p>

                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {LOGO_STYLES.map((item) => {
                    const selected = logoStyle === item.id;

                    return (
                      <button
                        key={item.id}
                        type="button"
                        disabled={submitting}
                        onClick={() => setLogoStyle(item.id)}
                        className={`relative rounded-xl border p-4 text-left transition ${
                          selected
                            ? "border-violet-500 bg-violet-50 ring-1 ring-violet-500"
                            : "border-zinc-200 bg-white hover:-translate-y-0.5 hover:border-zinc-300 hover:shadow-sm"
                        }`}
                      >
                        <span
                          className={`flex h-9 w-9 items-center justify-center rounded-lg text-base font-semibold ${
                            selected
                              ? "bg-violet-600 text-white"
                              : "bg-zinc-100 text-zinc-600"
                          }`}
                        >
                          {item.preview}
                        </span>

                        <span className="mt-3 block text-sm font-semibold text-zinc-900">
                          {item.name}
                        </span>

                        <span className="mt-1 block text-[10px] leading-4 text-zinc-400">
                          {item.description}
                        </span>

                        {selected && (
                          <span className="absolute right-3 top-3 text-xs font-bold text-violet-600">
                            ✓
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            </FormSection>

            {/* Section 3 */}
            <FormSection
              number="03"
              title="Choose your colors"
              description="Pick a starting palette or define your own brand colors."
            >
              <div className="grid gap-3 sm:grid-cols-2">
                {PALETTES.map((item) => {
                  const selected =
                    !useCustomColors && palette === item.id;

                  return (
                    <button
                      key={item.id}
                      type="button"
                      disabled={submitting}
                      onClick={() => {
                        setPalette(item.id);
                        setUseCustomColors(false);
                      }}
                      className={`flex items-center justify-between rounded-xl border p-4 text-left transition ${
                        selected
                          ? "border-violet-500 bg-violet-50 ring-1 ring-violet-500"
                          : "border-zinc-200 bg-white hover:border-zinc-300"
                      }`}
                    >
                      <span className="text-sm font-semibold text-zinc-800">
                        {item.name}
                      </span>

                      <span className="flex -space-x-1">
                        {item.colors.map((color) => (
                          <span
                            key={color}
                            className="h-7 w-7 rounded-full border-2 border-white shadow-sm"
                            style={{
                              backgroundColor: color,
                            }}
                          />
                        ))}
                      </span>
                    </button>
                  );
                })}
              </div>

              <div className="mt-5 rounded-xl border border-zinc-200 bg-zinc-50/70 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-zinc-800">
                      Custom colors
                    </p>

                    <p className="mt-1 text-xs text-zinc-400">
                      Use your own exact brand colors.
                    </p>
                  </div>

                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() =>
                      setUseCustomColors((current) => !current)
                    }
                    className={`relative h-6 w-11 rounded-full transition ${
                      useCustomColors
                        ? "bg-violet-600"
                        : "bg-zinc-300"
                    }`}
                  >
                    <span
                      className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow transition ${
                        useCustomColors ? "left-6" : "left-1"
                      }`}
                    />
                  </button>
                </div>

                {useCustomColors && (
                  <div className="mt-4 flex flex-wrap gap-4">
                    {customColors.map((color, index) => (
                      <label
                        key={index}
                        className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white p-2"
                      >
                        <input
                          type="color"
                          value={color}
                          disabled={submitting}
                          onChange={(event) => {
                            const updated = [...customColors];
                            updated[index] = event.target.value;
                            setCustomColors(updated);
                          }}
                          className="h-8 w-8 cursor-pointer border-0 bg-transparent"
                        />

                        <span className="font-mono text-xs uppercase text-zinc-500">
                          {color}
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </FormSection>

            {/* Section 4 */}
            <FormSection
              number="04"
              title="Creative direction"
              description="Optional instructions give you more control over what the AI explores."
            >
              <Field
                label="Anything specific in mind?"
                hint="Optional"
              >
                <textarea
                  value={creativeDirection}
                  onChange={(event) =>
                    setCreativeDirection(event.target.value)
                  }
                  disabled={submitting}
                  rows={4}
                  maxLength={600}
                  placeholder='e.g. "Use the letter N, avoid generic technology symbols, and keep the mark suitable for an app icon."'
                  className={`${inputClass} h-auto resize-none py-3.5`}
                />
              </Field>

              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  "Avoid generic icons",
                  "Suitable for social media",
                  "Strong monogram",
                  "Simple geometry",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    disabled={submitting}
                    onClick={() =>
                      setCreativeDirection((current) =>
                        current
                          ? `${current} ${suggestion}.`
                          : `${suggestion}.`
                      )
                    }
                    className="rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-[11px] font-medium text-zinc-500 transition hover:border-violet-200 hover:text-violet-600"
                  >
                    + {suggestion}
                  </button>
                ))}
              </div>
            </FormSection>
          </div>

          {/* Sidebar */}
          <aside className="lg:sticky lg:top-24 lg:self-start">
            <div className="overflow-hidden rounded-[22px] border border-white/90 bg-white/90 shadow-[0_20px_60px_rgba(79,70,229,0.08)] backdrop-blur-xl">
              <div className="border-b border-zinc-100 p-5">
                <p className="text-sm font-semibold text-zinc-900">
                  Your creative brief
                </p>

                <p className="mt-1 text-xs text-zinc-400">
                  Review before generation.
                </p>
              </div>

              {/* Preview */}
              <div className="p-5">
                <div className="relative flex h-36 items-center justify-center overflow-hidden rounded-xl bg-zinc-50">
                  <div className="absolute inset-0 opacity-[0.03] [background-image:linear-gradient(#000_1px,transparent_1px),linear-gradient(90deg,#000_1px,transparent_1px)] [background-size:16px_16px]" />

                  <div className="relative text-center">
                    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-950 text-xl font-semibold uppercase text-white shadow-lg">
                      {businessName.trim().slice(0, 1) || "B"}
                    </div>

                    <p className="mt-3 max-w-[230px] truncate text-sm font-semibold text-zinc-800">
                      {businessName || "Your brand"}
                    </p>
                  </div>
                </div>

                <div className="mt-5 space-y-4">
                  <BriefItem
                    label="Industry"
                    value={industry || "Not selected"}
                  />

                  <BriefItem
                    label="Style"
                    value={
                      LOGO_STYLES.find(
                        (item) => item.id === logoStyle
                      )?.name || logoStyle
                    }
                  />

                  <BriefItem
                    label="Concepts"
                    value={`${conceptCount} directions`}
                  />

                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                      Colors
                    </p>

                    <div className="mt-2 flex gap-2">
                      {(useCustomColors
                        ? customColors
                        : selectedPalette?.colors || []
                      ).map((color) => (
                        <span
                          key={color}
                          className="h-7 flex-1 rounded-lg border border-black/5 shadow-sm"
                          style={{
                            backgroundColor: color,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {error && (
                  <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-3 text-xs leading-5 text-red-700">
                    {error}
                  </div>
                )}

                {submitting && (
                  <div className="mt-5 rounded-xl border border-violet-100 bg-violet-50 p-4">
                    <div className="flex items-center gap-2">
                      <div className="studio-spinner h-4 w-4 rounded-full border-2 border-violet-200 border-t-violet-600" />

                      <p className="text-xs font-semibold text-zinc-700">
                        {stage === "brand" &&
                          "Building brand strategy..."}

                        {stage === "logos" &&
                          `Creating ${conceptCount} concepts...`}

                        {stage === "complete" &&
                          "Opening Brand Studio..."}
                      </p>
                    </div>

                    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-violet-100">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-violet-600 to-indigo-500 transition-all duration-700"
                        style={{
                          width: `${progress}%`,
                        }}
                      />
                    </div>

                    <p className="mt-2 text-[10px] leading-4 text-zinc-400">
                      Local AI generation may take a little longer for
                      larger concept sets.
                    </p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="mt-6 flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-zinc-950 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-zinc-800 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting
                    ? "Creating your brand..."
                    : `Generate ${conceptCount} concepts`}

                  {!submitting && <span>→</span>}
                </button>

                <div className="mt-4 flex items-center justify-center gap-2 text-[10px] text-zinc-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Local AI · No external image API required
                </div>
              </div>
            </div>
          </aside>
        </div>
      </form>
    </main>
  );
}

const inputClass =
  "h-12 w-full rounded-xl border border-zinc-200 bg-white px-4 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 hover:border-zinc-300 focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10 disabled:bg-zinc-50 disabled:opacity-60";

function FormSection({
  number,
  title,
  description,
  children,
}: {
  number: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-[22px] border border-white/90 bg-white/90 shadow-[0_10px_35px_rgba(24,24,27,0.04)] backdrop-blur-xl">
      <div className="flex gap-4 border-b border-zinc-100 px-6 py-5">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-violet-50 text-[10px] font-semibold text-violet-600">
          {number}
        </span>

        <div>
          <h2 className="text-base font-semibold text-zinc-900">
            {title}
          </h2>

          <p className="mt-1 text-xs leading-5 text-zinc-400">
            {description}
          </p>
        </div>
      </div>

      <div className="p-6">{children}</div>
    </section>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-2 flex items-center justify-between gap-4">
        <span className="text-sm font-semibold text-zinc-800">
          {label}
        </span>

        {hint && (
          <span className="text-[11px] font-normal text-zinc-400">
            {hint}
          </span>
        )}
      </span>

      {children}
    </label>
  );
}

function BriefItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start justify-between gap-5 border-b border-zinc-100 pb-3">
      <span className="text-xs text-zinc-400">{label}</span>

      <span className="max-w-[180px] text-right text-xs font-semibold text-zinc-700">
        {value}
      </span>
    </div>
  );
}