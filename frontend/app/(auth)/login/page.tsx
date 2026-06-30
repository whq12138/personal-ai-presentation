"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Presentation, LogIn, Mail, Lock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/lib/auth/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {/* Logo */}
      <div className="flex items-center justify-center gap-3 mb-8">
        <div className="w-10 h-10 bg-gradient-to-br from-[#64FFDA] to-[#45E0BE] rounded-xl flex items-center justify-center">
          <Presentation className="w-5 h-5 text-[#0A192F]" />
        </div>
        <div className="text-xl font-bold text-[#E6F1FF]">
          Personal AI<span className="text-[#64FFDA]"> Presentation</span>
        </div>
      </div>

      {/* Card */}
      <div className="bg-[#112240] border border-[#64FFDA]/10 rounded-2xl p-8">
        <h1 className="text-xl font-bold text-[#E6F1FF] mb-2">Welcome back</h1>
        <p className="text-sm text-[#8892B0] mb-6">
          Sign in to your account to continue
        </p>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400 mb-4">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#8892B0] mb-1.5">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#495670]" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-[#0A192F] border border-[#64FFDA]/10 rounded-xl text-[#E6F1FF] pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#64FFDA]/30 transition-all"
                placeholder="you@example.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#8892B0] mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#495670]" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-[#0A192F] border border-[#64FFDA]/10 rounded-xl text-[#E6F1FF] pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#64FFDA]/30 transition-all"
                placeholder="••••••••"
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            isLoading={isLoading}
            leftIcon={!isLoading ? <LogIn className="w-4 h-4" /> : undefined}
          >
            Sign In
          </Button>
        </form>

        <p className="text-sm text-center text-[#495670] mt-6">
          Don't have an account?{" "}
          <Link href="/register" className="text-[#64FFDA] hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
