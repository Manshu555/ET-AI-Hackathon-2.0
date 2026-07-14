"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { motion, AnimatePresence } from "framer-motion";
import Loader from "@/components/Loader";

const ROLES = [
  { value: "engineer", emoji: "🔧", label: "Engineer", desc: "Design & build systems" },
  { value: "qa_lead", emoji: "✅", label: "QA Lead", desc: "Quality assurance & testing" },
  { value: "project_manager", emoji: "📊", label: "Project Manager", desc: "Oversee project delivery" },
  { value: "admin", emoji: "🔑", label: "Admin", desc: "Full system access" },
];

export default function AuthModal({
  isOpen,
  onClose,
  initialMode = "login",
}: {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: "login" | "signup";
}) {
  const [mode, setMode] = useState<"login" | "signup">(initialMode);
  
  // Login State
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  
  // Signup State
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState("engineer");
  const [roleOpen, setRoleOpen] = useState(false);
  
  // General State
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  const router = useRouter();
  const { login, register, googleLogin } = useAuth();

  useEffect(() => {
    if (isOpen) setMode(initialMode);
  }, [isOpen, initialMode]);

  const validateEmail = (e: string): boolean => {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|hotmail\.com|protonmail\.com|icloud\.com|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$/i;
    return emailRegex.test(e);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(loginEmail, loginPassword);
      onClose();
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) return setError("Full Name is required");
    if (!email.trim()) return setError("Email is required");
    if (!validateEmail(email)) return setError("Please enter a valid email (e.g. name@gmail.com)");
    if (password.length < 8) return setError("Password must be at least 8 characters");
    if (password !== confirmPassword) return setError("Passwords do not match");

    setLoading(true);
    try {
      await register(name, email, password, role);
      onClose();
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    setError("");
    setLoading(true);
    try {
      await googleLogin();
      onClose();
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Google authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const selectedRole = ROLES.find((r) => r.value === role);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", bounce: 0.3, duration: 0.4 }}
            className="auth-container"
          >
            {/* Loading Overlay */}
            {loading && (
              <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/70 backdrop-blur-sm rounded-[35px]">
                <Loader text={mode === "login" ? "Signing In" : "Creating Account"} />
              </div>
            )}

            {/* Header / Tabs */}
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-gray-100">
              <div className="flex gap-4">
                <button 
                  onClick={() => { setMode("login"); setError(""); }}
                  className={`text-xl font-black transition-colors ${mode === "login" ? "text-[#1089D3]" : "text-gray-400 hover:text-gray-600"}`}
                >
                  Sign In
                </button>
                <button 
                  onClick={() => { setMode("signup"); setError(""); }}
                  className={`text-xl font-black transition-colors ${mode === "signup" ? "text-[#1089D3]" : "text-gray-400 hover:text-gray-600"}`}
                >
                  Sign Up
                </button>
              </div>
              <button 
                onClick={onClose}
                className="p-1 text-gray-400 transition-colors rounded-full hover:text-gray-700 hover:bg-gray-100"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>

            <div>
              {error && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="auth-error">
                  {error}
                </motion.div>
              )}

              <AnimatePresence mode="wait">
                {mode === "login" ? (
                  <motion.form 
                    key="login"
                    initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2 }}
                    onSubmit={handleLogin} 
                    className="space-y-4"
                  >
                    <input className="auth-input" type="email" placeholder="Email *" value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} required />
                    <input className="auth-input" type="password" placeholder="Password *" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} required />
                    
                    <div className="auth-forgot">
                      <a href="#">Forgot Password?</a>
                    </div>
                    
                    <button type="submit" className="auth-submit-btn">Sign In</button>
                  </motion.form>
                ) : (
                  <motion.form 
                    key="signup"
                    initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                    onSubmit={handleSignup} 
                    className="space-y-4"
                  >
                    <input className="auth-input" type="text" placeholder="Full Name *" value={name} onChange={(e) => setName(e.target.value)} required />
                    <input className="auth-input" type="email" placeholder="Email (e.g. name@gmail.com) *" value={email} onChange={(e) => setEmail(e.target.value)} required />
                    <input className="auth-input" type="password" placeholder="Password (min 8 characters) *" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
                    <input className="auth-input" type="password" placeholder="Confirm Password *" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
                    
                    {confirmPassword && password !== confirmPassword && (
                      <p className="auth-field-error">⚠ Passwords do not match</p>
                    )}

                    {/* Role Accordion */}
                    <div className="auth-accordion">
                      <button type="button" className="auth-accordion-header" onClick={() => setRoleOpen(!roleOpen)}>
                        <span>{selectedRole?.emoji} {selectedRole?.label}</span>
                        <svg className={`auth-accordion-arrow ${roleOpen ? "auth-accordion-arrow-open" : ""}`} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6" /></svg>
                      </button>
                      {roleOpen && (
                        <div className="auth-accordion-body">
                          {ROLES.map((r) => (
                            <button key={r.value} type="button" className={`auth-accordion-option ${role === r.value ? "auth-accordion-option-active" : ""}`} onClick={() => { setRole(r.value); setRoleOpen(false); }}>
                              <span className="auth-accordion-option-emoji">{r.emoji}</span>
                              <div>
                                <div className="auth-accordion-option-label">{r.label}</div>
                                <div className="auth-accordion-option-desc">{r.desc}</div>
                              </div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    <button type="submit" className="auth-submit-btn">Create Account</button>
                  </motion.form>
                )}
              </AnimatePresence>

              <div className="mt-6 auth-social-container">
                <span className="auth-social-title">Or continue with</span>
                <div className="auth-social-accounts">
                  <button className="auth-social-button auth-google-btn" title="Continue with Google" onClick={handleGoogleAuth} type="button">
                    <svg className="auth-social-svg" xmlns="http://www.w3.org/2000/svg" height="20" width="20" viewBox="0 0 488 512">
                      <path d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
