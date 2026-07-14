"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useEffect, useState } from "react";
import AuthModal from "@/components/AuthModal";

export default function LandingPage() {
  const { user } = useAuth();
  const router = useRouter();
  
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<"login" | "signup">("login");

  const openAuthModal = (mode: "login" | "signup") => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  // If already logged in, redirect to dashboard
  useEffect(() => {
    if (user) {
      router.push("/dashboard");
    }
  }, [user, router]);

  return (
    <div className="landing-page">
      {/* Header */}
      <header className="landing-header">
        <div className="landing-header-inner">
          <Link href="/" className="landing-logo">
            <div className="landing-logo-icon">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <span className="landing-logo-text">EPC-Intel</span>
          </Link>
          <nav className="landing-nav">
            <button onClick={() => openAuthModal("login")} className="landing-btn">
              Login
            </button>
            <button onClick={() => openAuthModal("signup")} className="landing-btn landing-btn-primary">
              Sign Up
            </button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        {/* Animated background blobs */}
        <div className="landing-blob landing-blob-1"></div>
        <div className="landing-blob landing-blob-2"></div>
        <div className="landing-blob landing-blob-3"></div>

        <div className="landing-hero-content">
          <h1 className="landing-hero-title">
            AI Intelligence Platform for
            <span className="landing-gradient-text"> Data Centre EPC</span>
          </h1>
          <p className="landing-hero-subtitle">
            Automate compliance checking, schedule risk analysis, supply chain tracking,
            and knowledge management — all powered by Gemini AI.
          </p>
          <div className="landing-hero-actions">
            <button onClick={() => openAuthModal("signup")} className="landing-btn landing-btn-hero">
              Get Started
            </button>
            <button onClick={() => openAuthModal("login")} className="landing-btn landing-btn-outline">
              Sign In →
            </button>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="landing-features">
          <div className="landing-feature-card">
            <div className="landing-feature-icon" style={{ background: "linear-gradient(135deg, #3b82f6, #8b5cf6)" }}>
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h3>Compliance Agent</h3>
            <p>AI-powered submittal-vs-spec comparison with deterministic numeric rules</p>
          </div>
          <div className="landing-feature-card">
            <div className="landing-feature-icon" style={{ background: "linear-gradient(135deg, #10b981, #06b6d4)" }}>
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3>Schedule Risk</h3>
            <p>ML-driven critical path analysis and delay prediction for EPC projects</p>
          </div>
          <div className="landing-feature-card">
            <div className="landing-feature-icon" style={{ background: "linear-gradient(135deg, #f59e0b, #ef4444)" }}>
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3>RFI Knowledge Chat</h3>
            <p>RAG-powered Q&A over all your project documents with citations</p>
          </div>
          <div className="landing-feature-card">
            <div className="landing-feature-icon" style={{ background: "linear-gradient(135deg, #ec4899, #8b5cf6)" }}>
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3>Document Ingestion</h3>
            <p>Upload PDFs, auto-chunk, embed and index for instant AI retrieval</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>© 2026 EPC-Intel — Built for ET AI Hackathon 2.0</p>
      </footer>

      {/* Auth Modal */}
      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)} 
        initialMode={authModalMode} 
      />
    </div>
  );
}
