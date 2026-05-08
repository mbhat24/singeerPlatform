"use client";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { Music } from "lucide-react";

export function AuthScreen() {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  async function handleSubmit(e) {
    e.preventDefault(); setError(""); setSubmitting(true);
    try {
      if (mode === "login") await login(email, password);
      else await signup(email, password, name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally { setSubmitting(false); }
  }
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-600/20 border border-brand-500/30 mb-4">
            <Music className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Singer Platform</h1>
          <p className="text-zinc-400 mt-2">Sing in your own voice with AI</p>
        </div>
        <div className="glass rounded-2xl p-6">
          <div className="flex mb-6 bg-zinc-800 rounded-lg p-1">
            <button onClick={() => setMode("login")} className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${mode === "login" ? "bg-zinc-700 text-white" : "text-zinc-400"}`}>Sign In</button>
            <button onClick={() => setMode("signup")} className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${mode === "signup" ? "bg-zinc-700 text-white" : "text-zinc-400"}`}>Sign Up</button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "signup" && (
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">Name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} required className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500" placeholder="Your name" />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white" placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white" placeholder="Min 6 characters" />
            </div>
            {error && <div className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">{error}</div>}
            <button type="submit" disabled={submitting} className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-medium rounded-lg transition-colors">
              {submitting ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
