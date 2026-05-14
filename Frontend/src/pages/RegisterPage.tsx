import { Link } from "react-router-dom";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { ShieldCheck } from "lucide-react";

export function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#080b10] px-5 py-10">
      <div className="w-full max-w-md">
        <div className="mb-7">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg border border-teal-300/25 bg-teal-300/10 text-teal-300">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-teal-300/80">NEXUS</p>
          <h1 className="mt-3 text-2xl font-semibold text-white">Create your organization account</h1>
          <p className="mt-2 text-sm leading-relaxed text-white/45">
            Join a governed knowledge environment built for secure multimodal discovery.
          </p>
        </div>

        <div className="section-panel rounded-lg p-6 shadow-2xl">
          <RegisterForm />
          <p className="mt-5 text-center text-sm text-white/40">
            Already have an account?{" "}
            <Link to="/login" className="text-teal-300 hover:text-teal-200 transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
