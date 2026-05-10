import { useEffect } from "react";
import { useNavigate } from "react-router";
import { DashboardHeader, SIMULATOR_NAV } from "../components/DashboardHeader";
import { Sidebar } from "../components/dashboard/Sidebar";
import { RecommendedCourses } from "../components/dashboard/RecommendedCourses";
import { AboutSection } from "../components/AboutSection";
import { Footer } from "../components/Footer";
import { ChatbotFAB } from "../components/ChatbotFAB";
import { useAppData, toCourseData } from "../context/AppDataContext";

export function RecommendationsPage() {
  const { appData } = useAppData();
  const navigate    = useNavigate();

  useEffect(() => {
    if (!appData) navigate("/", { replace: true });
  }, [appData, navigate]);

  if (!appData) return null;

  const topCourses = appData.topRecommended.map(c => toCourseData(c));
  const altCourses = appData.alternativeCourses.map(c => toCourseData(c));

  // Build chatbot context so the AI knows what the user is looking at
  const recContext = (() => {
    const topLines = topCourses.map(c => {
      const probs    = c.grade_probabilities ?? {};
      const dominant = Object.entries(probs).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "?";
      return `  - ${c.code} | ${c.name} (${c.creditHours} cr) — most likely outcome: ${dominant}`;
    }).join("\n");
    const altLines = altCourses
      .map(c => `  - ${c.code} | ${c.name} (${c.creditHours} cr)`)
      .join("\n");
    return [
      "User is viewing the Course Recommendations page.",
      `ML Top Recommended Courses (${topCourses.length}):`,
      topLines  || "  None",
      `Alternative Courses (${altCourses.length}):`,
      altLines  || "  None",
      `Total recommended credit hours: ${appData.totalRecommendedHours}.`,
      `Academic status: ${appData.academicStatus}.`,
    ].join("\n");
  })();

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
        <Sidebar activePage="recommendations" />

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
            <p style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-accent)",
              fontWeight: 700,
              fontSize: "0.78rem",
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              marginBottom: "0.25rem",
            }}>
              Personalized for you
            </p>
            <h1 style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-dark)",
              fontWeight: 800,
              fontSize: "1.75rem",
            }}>
              Course Recommendations
            </h1>
            <p style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-heading)",
              fontWeight: 500,
              fontSize: "0.95rem",
              marginTop: "0.35rem",
            }}>
              Courses are ranked by your predicted success rate. Top picks fit your current load; alternatives are available if you want more options.
            </p>
          </div>

          <div style={{
            height: "1px",
            backgroundColor: "var(--lp-bg-secondary)",
            borderRadius: "9999px",
            margin: "1.25rem 0",
          }} />

          <RecommendedCourses topCourses={topCourses} altCourses={altCourses} />
        </main>
      </div>

      <AboutSection />
      <Footer />
      <ChatbotFAB pageContext={recContext} />
    </div>
  );
}


