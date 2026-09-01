"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";


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


export default function CreateBrandPage() {

  const router = useRouter();

  const [businessName, setBusinessName] =
    useState("");

  const [description, setDescription] =
    useState("");

  const [industry, setIndustry] =
    useState("");

  const [style, setStyle] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");


  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {

    event.preventDefault();

    setSubmitting(true);
    setError("");


    try {

      const response = await fetch(
        "http://127.0.0.1:8000/brand",
        {
          method: "POST",

          headers: {
            "Content-Type":
            "application/json",
          },

          body: JSON.stringify({
            business_name:
            businessName.trim(),

            description:
            description.trim(),

            industry,

            style,
          }),
        }
      );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Could not create brand"
        );

      }


      router.push(
        `/projects/${data.project.id}`
      );


    } catch (error) {

      console.error(error);

      setError(
        error instanceof Error
          ? error.message
          : "Could not create brand."
      );

      setSubmitting(false);

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
            className="text-slate-400 hover:text-white"
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
          Enter your company information.
          Your logo concepts and colour
          palettes will be generated automatically.
        </p>


        <form
          onSubmit={handleSubmit}
          className="mt-10 space-y-6 rounded-2xl border border-slate-800 bg-slate-900 p-8"
        >

          <div>

            <label className="mb-2 block font-medium">
              Business Name
            </label>

            <input
              value={businessName}
              onChange={(event) =>
                setBusinessName(
                  event.target.value
                )
              }
              required
              disabled={submitting}
              placeholder="Example: Nova Technologies"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-violet-500"
            />

          </div>


          <div>

            <label className="mb-2 block font-medium">
              Industry
            </label>

            <select
              value={industry}
              onChange={(event) =>
                setIndustry(
                  event.target.value
                )
              }
              required
              disabled={submitting}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3"
            >

              <option value="">
                Select industry
              </option>

              {INDUSTRIES.map(
                (item) => (

                  <option
                    key={item.value}
                    value={item.value}
                  >
                    {item.label}
                  </option>

                )
              )}

            </select>

          </div>


          <div>

            <label className="mb-2 block font-medium">
              Business Description
            </label>

            <textarea
              value={description}
              onChange={(event) =>
                setDescription(
                  event.target.value
                )
              }
              required
              rows={5}
              disabled={submitting}
              placeholder="Describe your company, products and customers..."
              className="w-full resize-none rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-violet-500"
            />

          </div>


          <div>

            <label className="mb-2 block font-medium">
              Brand Style
            </label>

            <select
              value={style}
              onChange={(event) =>
                setStyle(
                  event.target.value
                )
              }
              required
              disabled={submitting}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3"
            >

              <option value="">
                Select style
              </option>

              {STYLES.map(
                (item) => (

                  <option
                    key={item.value}
                    value={item.value}
                  >
                    {item.label}
                  </option>

                )
              )}

            </select>

          </div>


          {error && (

            <div className="rounded-lg border border-red-800 bg-red-950/40 p-4 text-red-300">
              {error}
            </div>

          )}


          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-violet-600 px-5 py-3 font-semibold hover:bg-violet-500 disabled:opacity-50"
          >

            {submitting
              ? "Creating Brand Identity..."
              : "Generate My Brand"}

          </button>


          {submitting && (

            <p className="text-center text-sm text-slate-400">
              Generating three logo concepts and
              analysing their colours...
            </p>

          )}

        </form>

      </section>

    </main>
  );
}