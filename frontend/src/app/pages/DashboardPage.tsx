import { useEffect } from "react";
import { useNavigate } from "react-router";
import { DashboardHeader, SIMULATOR_NAV } from "../components/DashboardHeader";
import { Sidebar } from "../components/dashboard/Sidebar";
import { StatsCards } from "../components/dashboard/StatsCards";
import { AboutSection } from "../components/AboutSection";
import { Footer } from "../components/Footer";
import { ChatbotFAB } from "../components/ChatbotFAB";
import { useAppData } from "../context/AppDataContext";

// â”€â”€ Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export function DashboardPage() {
  const { appData } = useAppData();
  const navigate    = useNavigate();

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
      <DashboardHeader navItems={SIMULATOR_NAV} />

      <div style={{ display: "flex", alignItems: "flex-start" }}>
        <Sidebar activePage="dashboard" />

        <main
          style={{
            flex: 1,
            minWidth: 0,
            padding: "1.75rem 2rem 3rem",
            backgroundColor: "var(--lp-bg-card)",
          }}
        >
          <StatsCards />
        </main>
      </div>

      <AboutSection />
      <Footer />
      <ChatbotFAB />
    </div>
  );
}


