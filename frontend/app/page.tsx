import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">

      {/* Navigation Bar */}
      <nav className="flex items-center justify-between border-b border-slate-800 px-10 py-5">

        <h1 className="text-2xl font-bold text-violet-400">
          BrandAI
        </h1>

        <div className="flex gap-6 text-slate-300">
          <a href="#features" className="hover:text-white">
            Features
          </a>

          <a href="#about" className="hover:text-white">
            About
          </a>
        </div>

      </nav>


      {/* Hero Section */}
      <section className="flex min-h-[80vh] flex-col items-center justify-center px-6 text-center">

        <p className="mb-4 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-sm text-violet-300">
          AI-Powered Brand Creation
        </p>

        <h2 className="max-w-4xl text-5xl font-bold leading-tight md:text-7xl">
          Build your brand
          <span className="text-violet-400"> with AI</span>
        </h2>

        <p className="mt-6 max-w-2xl text-lg text-slate-400">
          Transform a simple business idea into professional logos,
          brand colors, and promotional videos powered by artificial
          intelligence.
        </p>

        <Link
          href="/create"
          className="mt-8 rounded-xl bg-violet-600 px-8 py-4 font-semibold transition hover:bg-violet-500"
        >
          Create Your Brand
        </Link>

      </section>


      {/* Features Section */}
      <section
        id="features"
        className="border-t border-slate-800 px-10 py-20"
      >

        <h2 className="mb-12 text-center text-3xl font-bold">
          Everything you need to build your brand
        </h2>

        <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-3">

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-7">
            <h3 className="mb-3 text-xl font-semibold text-violet-400">
              AI Logo Generation
            </h3>

            <p className="text-slate-400">
              Generate unique logo concepts from a simple description
              of your business.
            </p>
          </div>


          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-7">
            <h3 className="mb-3 text-xl font-semibold text-violet-400">
              Smart Brand Kit
            </h3>

            <p className="text-slate-400">
              Automatically extract a cohesive color palette and
              branding information.
            </p>
          </div>


          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-7">
            <h3 className="mb-3 text-xl font-semibold text-violet-400">
              Promotional Videos
            </h3>

            <p className="text-slate-400">
              Transform your generated branding into short AI-powered
              promotional videos.
            </p>
          </div>

        </div>

      </section>

    </main>
  );
}