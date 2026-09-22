import Link from "next/link";

const features = [
  {
    number: "01",
    title: "AI logo directions",
    description:
      "Explore distinct logo concepts developed around your business, audience and brand personality.",
    accent: "bg-violet-100 text-violet-700",
  },
  {
    number: "02",
    title: "Complete brand identity",
    description:
      "Turn your selected concept into a cohesive system of colors, typography, messaging and brand intelligence.",
    accent: "bg-blue-100 text-blue-700",
  },
  {
    number: "03",
    title: "Promotional content",
    description:
      "Extend your identity into ready-to-use promotional assets and AI-generated brand videos.",
    accent: "bg-amber-100 text-amber-700",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#f7f7f8] text-zinc-900">
      {/* Navigation */}
      <header className="relative z-30 border-b border-zinc-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-950 text-sm font-bold text-white">
              B
            </div>

            <span className="text-[15px] font-semibold tracking-tight">
              BrandAI
            </span>
          </Link>

          <nav className="hidden items-center gap-7 md:flex">
            <a
              href="#features"
              className="text-sm font-medium text-zinc-500 transition hover:text-zinc-950"
            >
              Features
            </a>

            <a
              href="#how-it-works"
              className="text-sm font-medium text-zinc-500 transition hover:text-zinc-950"
            >
              How it works
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <Link
              href="/dashboard"
              className="hidden rounded-lg px-3 py-2 text-sm font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-950 sm:inline-flex"
            >
              Dashboard
            </Link>

            <Link
              href="/create"
              className="inline-flex h-9 items-center justify-center rounded-lg bg-zinc-950 px-4 text-sm font-semibold text-white transition hover:bg-zinc-800"
            >
              Create a brand
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative">
        <div className="pointer-events-none absolute left-1/2 top-0 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-violet-200/25 blur-[120px]" />

        <div className="relative mx-auto max-w-7xl px-6 pb-20 pt-20 text-center lg:px-8 lg:pb-28 lg:pt-28">
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white px-3 py-1.5 text-xs font-semibold text-violet-700 shadow-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-500" />
            AI-powered creative studio
          </div>

          <h1 className="mx-auto mt-7 max-w-4xl text-5xl font-semibold leading-[1.02] tracking-[-0.055em] text-zinc-950 sm:text-6xl lg:text-7xl">
            From business idea to
            <span className="text-violet-600"> complete brand.</span>
          </h1>

          <p className="mx-auto mt-7 max-w-2xl text-base leading-7 text-zinc-500 sm:text-lg sm:leading-8">
            Build your visual identity with AI. Explore original logo
            directions, define your brand system, and create promotional
            content from one simple brief.
          </p>

          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/create"
              className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-zinc-950 px-6 text-sm font-semibold text-white shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition hover:-translate-y-0.5 hover:bg-zinc-800 sm:w-auto"
            >
              Start creating
              <span aria-hidden="true">→</span>
            </Link>

            <Link
              href="/dashboard"
              className="inline-flex h-12 w-full items-center justify-center rounded-xl border border-zinc-200 bg-white px-6 text-sm font-semibold text-zinc-700 shadow-sm transition hover:border-zinc-300 hover:bg-zinc-50 sm:w-auto"
            >
              View projects
            </Link>
          </div>

          <p className="mt-4 text-xs text-zinc-400">
            Create your first brand identity in minutes.
          </p>

          {/* Product preview */}
          <div className="relative mx-auto mt-16 max-w-5xl">
            <div className="absolute -inset-8 rounded-[40px] bg-gradient-to-b from-violet-100/60 to-transparent blur-2xl" />

            <div className="relative overflow-hidden rounded-[24px] border border-zinc-200 bg-white text-left shadow-[0_30px_90px_rgba(24,24,27,0.12)]">
              <div className="flex h-14 items-center border-b border-zinc-100 px-5">
                <div className="flex gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-zinc-200" />
                  <span className="h-2.5 w-2.5 rounded-full bg-zinc-200" />
                  <span className="h-2.5 w-2.5 rounded-full bg-zinc-200" />
                </div>

                <span className="mx-auto pr-12 text-xs font-medium text-zinc-400">
                  Brand Studio
                </span>
              </div>

              <div className="p-6 sm:p-8">
                <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                  <div>
                    <div className="flex gap-2">
                      <span className="rounded-full bg-violet-50 px-2.5 py-1 text-[10px] font-semibold text-violet-600">
                        Technology
                      </span>

                      <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-[10px] font-semibold text-zinc-500">
                        Modern
                      </span>
                    </div>

                    <h2 className="mt-3 text-2xl font-semibold tracking-tight text-zinc-950">
                      Nova Labs
                    </h2>

                    <p className="mt-1.5 text-xs text-zinc-400">
                      Three visual identity directions created for your brand.
                    </p>
                  </div>

                  <div className="h-9 rounded-lg border border-zinc-200 bg-white px-3 text-xs font-semibold leading-9 text-zinc-500">
                    Generate more
                  </div>
                </div>

                <div className="mt-7 grid gap-3 sm:grid-cols-3">
                  {[
                    {
                      mark: "N",
                      background: "#fafafa",
                      color: "#18181b",
                    },
                    {
                      mark: "N.",
                      background: "#18181b",
                      color: "#ffffff",
                    },
                    {
                      mark: "N/",
                      background: "#f1efff",
                      color: "#6755e7",
                    },
                  ].map((logo, index) => (
                    <div
                      key={index}
                      className="overflow-hidden rounded-xl border border-zinc-200 bg-white"
                    >
                      <div
                        className="flex aspect-[4/3] items-center justify-center"
                        style={{
                          backgroundColor: logo.background,
                          color: logo.color,
                        }}
                      >
                        <div className="text-4xl font-semibold tracking-[-0.08em]">
                          {logo.mark}
                        </div>
                      </div>

                      <div className="flex items-center justify-between border-t border-zinc-100 px-3.5 py-3">
                        <span className="text-[11px] font-semibold text-zinc-700">
                          Concept 0{index + 1}
                        </span>

                        {index === 1 ? (
                          <span className="rounded-full bg-violet-50 px-2 py-1 text-[9px] font-semibold text-violet-600">
                            Selected
                          </span>
                        ) : (
                          <span className="text-[9px] text-zinc-400">
                            Explore
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-[1fr_.7fr]">
                  <div className="rounded-xl border border-zinc-200 p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                      Brand colors
                    </p>

                    <div className="mt-4 flex gap-2">
                      <div className="h-10 flex-1 rounded-lg bg-[#18181b]" />
                      <div className="h-10 flex-1 rounded-lg bg-[#6755e7]" />
                      <div className="h-10 flex-1 rounded-lg bg-[#e3ddff]" />
                      <div className="h-10 flex-1 rounded-lg bg-[#f4f4f5]" />
                    </div>
                  </div>

                  <div className="rounded-xl border border-zinc-200 p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                      Typography
                    </p>

                    <p className="mt-3 text-xl font-semibold tracking-tight text-zinc-800">
                      Geist
                    </p>

                    <p className="text-[10px] text-zinc-400">
                      Modern · Clear · Digital
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section
        id="features"
        className="border-y border-zinc-200 bg-white"
      >
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-8 lg:py-24">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">
              Everything in one studio
            </p>

            <h2 className="mt-4 text-3xl font-semibold tracking-[-0.035em] text-zinc-950 sm:text-4xl">
              More than a logo generator.
            </h2>

            <p className="mt-4 text-base leading-7 text-zinc-500">
              Build the pieces of a real visual identity instead of
              stopping at a single generated image.
            </p>
          </div>

          <div className="mt-12 grid divide-y divide-zinc-200 border-y border-zinc-200 md:grid-cols-3 md:divide-x md:divide-y-0">
            {features.map((feature) => (
              <div
                key={feature.number}
                className="py-8 md:px-8 md:first:pl-0 md:last:pr-0"
              >
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl text-xs font-bold ${feature.accent}`}
                >
                  {feature.number}
                </div>

                <h3 className="mt-6 text-lg font-semibold tracking-tight text-zinc-950">
                  {feature.title}
                </h3>

                <p className="mt-3 text-sm leading-6 text-zinc-500">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Process */}
      <section id="how-it-works">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-8 lg:py-24">
          <div className="grid gap-14 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">
                Simple process
              </p>

              <h2 className="mt-4 max-w-md text-3xl font-semibold tracking-[-0.035em] text-zinc-950 sm:text-4xl">
                Your identity, from brief to brand system.
              </h2>

              <p className="mt-4 max-w-md text-sm leading-7 text-zinc-500">
                BrandAI handles the repetitive creative work while
                keeping you in control of the visual direction.
              </p>
            </div>

            <div className="space-y-3">
              {[
                [
                  "01",
                  "Describe your business",
                  "Share your name, industry, audience and preferred creative style.",
                ],
                [
                  "02",
                  "Explore visual directions",
                  "Compare distinct logo concepts and generate more until you find the right direction.",
                ],
                [
                  "03",
                  "Build your identity",
                  "Select a concept and generate the color, typography, messaging and promotional system around it.",
                ],
              ].map(([number, title, description]) => (
                <div
                  key={number}
                  className="flex gap-5 rounded-2xl border border-zinc-200 bg-white p-5"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-zinc-950 text-[11px] font-semibold text-white">
                    {number}
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-zinc-900">
                      {title}
                    </h3>

                    <p className="mt-1.5 text-sm leading-6 text-zinc-500">
                      {description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-20 lg:px-8">
        <div className="mx-auto max-w-7xl overflow-hidden rounded-[28px] bg-zinc-950 px-6 py-14 text-center text-white sm:px-10 sm:py-16">
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-white text-sm font-bold text-zinc-950">
            B
          </div>

          <h2 className="mx-auto mt-6 max-w-2xl text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">
            Give your business an identity.
          </h2>

          <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-zinc-400">
            Start with a simple business brief and turn it into a
            complete visual direction.
          </p>

          <Link
            href="/create"
            className="mt-7 inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-white px-5 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-100"
          >
            Create your brand
            <span>→</span>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-7 text-xs text-zinc-400 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <Link
            href="/"
            className="flex items-center gap-2 font-semibold text-zinc-700"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-zinc-950 text-[9px] text-white">
              B
            </span>
            BrandAI
          </Link>

          <span>AI-powered brand creation studio</span>
        </div>
      </footer>
    </main>
  );
}