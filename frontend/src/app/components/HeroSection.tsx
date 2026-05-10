import { ImageWithFallback } from "./figma/ImageWithFallback";
import { useNavigate } from "react-router";

export function HeroSection() {
  const navigate = useNavigate();
  return (
    <section
      id="home"
      style={{ backgroundColor: "var(--lp-bg-primary)" }}
      className="w-full py-24 px-6"
    >
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        {/* Left Column – Text */}
        <div className="flex flex-col">
          <h1
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-heading)",
              fontWeight: 800,
              fontSize: "clamp(2.4rem, 5vw, 3.5rem)",
              lineHeight: 1.2,
            }}
          >
            Maximize Your Grades.{" "}
            <span style={{ color: "var(--lp-text-dark)" }}>Minimize the Stress.</span>
          </h1>
          <p
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-dark)",
              fontWeight: 500,
              fontSize: "1.2rem",
              marginTop: "1.25rem",
              lineHeight: 1.7,
            }}
          >
            Let's make your academic journey perfectly suited to you.
          </p>

          <div className="flex gap-4 mt-8 flex-wrap">
            <button
              onClick={() => {
                const el = document.getElementById("upload");
                if (el) el.scrollIntoView({ behavior: "smooth" });
              }}
              style={{
                fontFamily: "'Nunito', sans-serif",
                backgroundColor: "#A8BE83",
                color: "#ffffff",
                fontWeight: 700,
                fontSize: "1rem",
                padding: "0.85rem 2.2rem",
                borderRadius: "9999px",
                border: "none",
                cursor: "pointer",
                boxShadow: "0 4px 18px rgba(168,190,131,0.45)",
                transition: "transform 0.15s, box-shadow 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = "0 8px 24px rgba(168,190,131,0.55)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 4px 18px rgba(168,190,131,0.45)";
              }}
            >
              Get Started
            </button>
            <button
              onClick={() => {
                const el = document.getElementById("how-it-works");
                if (el) el.scrollIntoView({ behavior: "smooth" });
              }}
              style={{
                fontFamily: "'Nunito', sans-serif",
                backgroundColor: "transparent",
                color: "var(--lp-text-heading)",
                fontWeight: 700,
                fontSize: "1rem",
                padding: "0.85rem 2.2rem",
                borderRadius: "9999px",
                border: "2px solid var(--lp-text-heading)",
                cursor: "pointer",
                transition: "background-color 0.15s, color 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "var(--lp-text-heading)";
                e.currentTarget.style.color = "#fff";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "transparent";
                e.currentTarget.style.color = "var(--lp-text-heading)";
              }}
            >
              How It Works
            </button>
          </div>
        </div>

        {/* Right Column – Illustration */}
        <div className="relative flex items-center justify-center">
          {/* Organic blob background */}
          <div
            style={{
              position: "absolute",
              width: "110%",
              height: "110%",
              background:
                "radial-gradient(ellipse at 60% 50%, #C2D0B9 0%, #EAE3CD 55%, transparent 80%)",
              borderRadius: "60% 40% 55% 45% / 50% 60% 40% 55%",
              zIndex: 0,
              filter: "blur(2px)",
              opacity: 0.4,
            }}
          />

          {/* Floating accent circles */}
          <div
            style={{
              position: "absolute",
              top: "8%",
              right: "6%",
              width: "70px",
              height: "70px",
              backgroundColor: "#A8BE83",
              borderRadius: "50%",
              opacity: 0.35,
              zIndex: 1,
            }}
          />
          <div
            style={{
              position: "absolute",
              bottom: "12%",
              left: "4%",
              width: "45px",
              height: "45px",
              backgroundColor: "#F2C27F",
              borderRadius: "50%",
              opacity: 0.45,
              zIndex: 1,
            }}
          />

          {/* Main image */}
          <div
            style={{
              position: "relative",
              zIndex: 2,
              borderRadius: "40% 60% 55% 45% / 45% 50% 60% 55%",
              overflow: "hidden",
              width: "100%",
              maxWidth: "480px",
              aspectRatio: "4/3",
              boxShadow: "0 20px 60px rgba(79,83,33,0.15)",
            }}
          >
            <ImageWithFallback
              src="https://images.unsplash.com/photo-1606295834251-36d654991797?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzdHVkZW50JTIwc3R1ZHlpbmclMjBkZXNrJTIwYm9va3MlMjBwcm9kdWN0aXZlfGVufDF8fHx8MTc3NzA4Mjg2NHww&ixlib=rb-4.1.0&q=80&w=1080"
              alt="Academic potential blooming – earthy study illustration"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
            <div
              style={{
                position: "absolute",
                inset: 0,
                background:
                  "linear-gradient(135deg, rgba(168,190,131,0.18) 0%, rgba(194,208,185,0.12) 100%)",
              }}
            />
          </div>

          {/* Floating badge */}
          <div
            style={{
              position: "absolute",
              bottom: "6%",
              right: "-2%",
              zIndex: 3,
              backgroundColor: "var(--lp-bg-card)",
              borderRadius: "1.5rem",
              padding: "0.75rem 1.1rem",
              boxShadow: "0 8px 24px rgba(79,83,33,0.14)",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <span style={{ fontSize: "1.4rem" }}>🎓</span>
            <div>
              <div
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--lp-text-dark)",
                  fontWeight: 700,
                  fontSize: "0.85rem",
                }}
              >
                GPA Optimized!
              </div>
              <div
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--lp-text-accent)",
                  fontWeight: 600,
                  fontSize: "0.75rem",
                }}
              >
                +0.4 this semester
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
