import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { DashboardHeader, SIMULATOR_NAV } from "../components/DashboardHeader";
import { Sidebar } from "../components/dashboard/Sidebar";
import { GPASimulator } from "../components/dashboard/GPASimulator";
import { AboutSection } from "../components/AboutSection";
import { Footer } from "../components/Footer";
import { ChatbotFAB } from "../components/ChatbotFAB";
import { useAppData } from "../context/AppDataContext";

export function SimulatorPage() {
  const { appData } = useAppData();
  const navigate    = useNavigate();
  const [simContext, setSimContext] = useState("User is on the GPA Simulator. No courses selected yet.");

  useEffect(() => {
    if (!appData) navigate("/", { replace: true });
  }, [appData, navigate]);

  if (!appData) return null;

  return (
    <div
      style={{
        fontFamily: "'Nunito', sans-serif",
        backgroundColor: "var(--lp-bg-card)",
        minHeight: "100vh",
        overflowX: "hidden",
      }}
    >
      {/* Header â€” Home + About only */}
      <DashboardHeader navItems={SIMULATOR_NAV} />

      {/* Body: Sidebar + Main */}
      <div style={{ display: "flex", alignItems: "flex-start" }}>
        {/* Sidebar â€” GPA Simulator active */}
        <Sidebar activePage="simulator" />

        {/* Main content */}
        <main
          style={{
            flex: 1,
            minWidth: 0,
            padding: "1.75rem 2rem 3rem",
            backgroundColor: "var(--lp-bg-card)",
          }}
        >
          {/* Page intro */}
          <div style={{ marginBottom: "0.5rem" }}>
            <p
              style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-accent)",
                fontWeight: 700,
                fontSize: "0.78rem",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                marginBottom: "0.25rem",
              }}
            >
              Plan your next semester
            </p>
            <h1
              style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-dark)",
                fontWeight: 800,
                fontSize: "1.75rem",
              }}
            >
              GPA Simulator
            </h1>
            <p
              style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-heading)",
                fontWeight: 500,
                fontSize: "0.95rem",
                marginTop: "0.35rem",
              }}
            >
              Toggle any recommended or alternative course to instantly see how it impacts your predicted GPA trend.
            </p>
          </div>

          {/* Divider */}
          <div
            style={{
              height: "1px",
              backgroundColor: "var(--lp-bg-secondary)",
              borderRadius: "9999px",
              margin: "1.25rem 0",
            }}
          />

          {/* The simulator itself */}
          <GPASimulator onContextChange={setSimContext} />
        </main>
      </div>

      {/* About Us section â€” exact same as landing page */}
      <AboutSection />

      <Footer />
      <ChatbotFAB pageContext={simContext} />
    </div>
  );
}


