import { useState } from "react";
import { signInWithGoogle } from "./lib/firebase";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(
    import.meta.env.VITE_FIREBASE_API_KEY
      ? ""
      : "Firebase authentication is not configured. Create frontend/.env and add VITE_FIREBASE_API_KEY."
  );

  async function handleLogin() {
    setLoading(true);
    setError("");

    try {
      await signInWithGoogle();
    } catch (err) {
      setError(err.message || "Google sign-in failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-mark">✚</div>
        <p className="auth-eyebrow">CLINIVUE SECURE WORKSPACE</p>
        <h1>Emergency response, thoughtfully connected.</h1>
        <p className="auth-copy">
          Sign in to access your ambulance routing dashboard, hospital
          recommendations, and dispatch operations.
        </p>
        <button className="google-button" onClick={handleLogin} disabled={loading}>
          <span className="google-icon">G</span>
          {loading ? "Signing you in..." : "Continue with Google"}
        </button>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <p className="auth-disclaimer">
          Your workspace is protected by Clinivue authentication.
        </p>
      </section>
    </main>
  );
}
