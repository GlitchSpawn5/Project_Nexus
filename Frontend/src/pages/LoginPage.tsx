import { Link } from "react-router-dom";
import { LoginForm } from "@/components/auth/LoginForm";
import { DatabaseZap, GitBranch, LockKeyhole, Route } from "lucide-react";
import LineWaves from "@/src/components/LineWaves";

export function LoginPage() {
  const signals = [
    { label: "Governed access", icon: LockKeyhole },
    { label: "Multimodal ingestion", icon: DatabaseZap },
    { label: "Evidence intelligence", icon: GitBranch },
    { label: "Provider resilience", icon: Route },
  ];

  return (
    <div className="min-h-screen bg-[#080b10] text-white">
      <div className="grid min-h-screen lg:grid-cols-[1.1fr_0.9fr]">
        <section className="relative flex min-h-[46rem] flex-col justify-between overflow-hidden border-r border-white/10 px-8 py-8 sm:px-12">
          <div className="absolute inset-0 opacity-70">
            <LineWaves
              speed={0.22}
              innerLineCount={30}
              outerLineCount={42}
              warpIntensity={0.85}
              rotation={-45}
              edgeFadeWidth={0}
              colorCycleSpeed={0.65}
              brightness={0.12}
              color1="#2dd4bf"
              color2="#60a5fa"
              color3="#f8fafc"
              enableMouseInteraction
              mouseInfluence={1.4}
            />
          </div>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_18%,rgba(45,212,191,0.16),transparent_34%),linear-gradient(90deg,rgba(8,11,16,0.58),rgba(8,11,16,0.82))]" />

          <div className="relative z-10">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-teal-300/80">
              NEXUS
            </p>
            <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight text-white sm:text-6xl">
              Knowledge intelligence for every team, file, and format.
            </h1>
          </div>

          <div className="relative z-10 grid gap-3 sm:grid-cols-2">
            {signals.map((item) => (
              <div key={item.label} className="section-panel rounded-lg p-4">
                <item.icon className="h-5 w-5 text-teal-300" />
                <p className="mt-3 text-sm font-medium text-white/85">{item.label}</p>
                <p className="mt-1 text-xs leading-relaxed text-white/42">
                  Designed for global teams that need secure search, contextual evidence, and
                  trustworthy AI answers.
                </p>
              </div>
            ))}
          </div>

          <div className="section-panel relative z-10 rounded-lg p-5">
            <div className="flex items-center gap-3 text-sm text-white/70">
              <span className="status-dot" />
              Platform environment ready
            </div>
            <div className="mt-4 grid grid-cols-3 gap-4 text-xs">
              <div>
                <p className="text-2xl font-semibold text-white">5</p>
                <p className="text-white/38">Retrieval layers</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-white">4</p>
                <p className="text-white/38">Governance roles</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-white">3</p>
                <p className="text-white/38">Provider routes</p>
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-5 py-10">
          <div className="w-full max-w-md">
            <div className="mb-7">
              <h2 className="text-2xl font-semibold text-white">Welcome back</h2>
              <p className="mt-2 text-sm leading-relaxed text-white/45">
                Access governed knowledge spaces, inspect cited answers, and uncover connected
                evidence across documents, images, and audio.
              </p>
            </div>

            <div className="section-panel rounded-lg p-6 shadow-2xl">
              <LoginForm />
              <p className="mt-5 text-center text-sm text-white/42">
                No account?{" "}
                <Link to="/register" className="text-teal-300 transition-colors hover:text-teal-200">
                  Register
                </Link>
              </p>
            </div>

            <p className="mt-4 rounded-lg border border-white/8 bg-white/[0.03] px-3 py-2 text-center text-xs text-white/35">
              Secure access for organizations, research teams, and operations groups.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
