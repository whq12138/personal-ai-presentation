"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Presentation, UserPlus, Mail, Lock, User, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth/AuthContext";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setIsLoading(true);
    try {
      await register(email, password, name || undefined);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-center gap-3 mb-8">
        <div className="w-10 h-10 bg-gradient-to-br from-[#64FFDA] to-[#45E0BE] rounded-xl flex items-center justify-center">
          <Presentation className="w-5 h-5 text-[#0A192F]" />
        </div>
        <div className="text-xl font-bold text-[#E6F1FF]">
          Personal AI<span className="text-[#64FFDA]"> Presentation</span>
        </div>
      </div>

      <div className="bg-[#112240] border border-[#64FFDA]/10 rounded-2xl p-8">
        <h1 className="text-xl font-bold text-[#E6F1FF] mb-2">Create account</h1>
        <p className="text-sm text-[#8892B0] mb-1">
          Start generating AI-powered presentations
        </p>
        <p className="text-xs text-[#FFD700]/70 mb-6 bg-[#FFD700]/5 border border-[#FFD700]/10 rounded-lg px-3 py-2">
          Free tier: 3 generations/hour, 10/day. Export included.
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
              Name (optional)
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#495670]" />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[#0A192F] border border-[#64FFDA]/10 rounded-xl text-[#E6F1FF] pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#64FFDA]/30 transition-all"
                placeholder="Your name"
              />
            </div>
          </div>

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
                minLength={8}
                className="w-full bg-[#0A192F] border border-[#64FFDA]/10 rounded-xl text-[#E6F1FF] pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#64FFDA]/30 transition-all"
                placeholder="Min. 8 characters"
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            isLoading={isLoading}
            leftIcon={!isLoading ? <UserPlus className="w-4 h-4" /> : undefined}
          >
            Create Account
          </Button>
        </form>

        <p className="text-sm text-center text-[#495670] mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-[#64FFDA] hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
