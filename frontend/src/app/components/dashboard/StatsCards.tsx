import { GraduationCap } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import { useIsMobile } from "../ui/use-mobile";

// ── Helpers ───────────────────────────────────────────────────────────────────
function getGPAColor(gpa: number): string {
  if (gpa >= 3.0) return "#9CA35A";
  if (gpa >= 2.5) return "#F2C27F";
  return "#C87330";
}

function getStandingConfig(cgpa: number): { label: string; color: string; bg: string; emoji: string } {
  if (cgpa >= 3.0) return { label: "Excellent Standing", color: "var(--lp-text-accent)", bg: "#E8F0DC", emoji: "🏆" };
  if (cgpa >= 2.5) return { label: "Good Standing",      color: "var(--lp-text-accent)", bg: "#E8F0DC", emoji: "✅" };
  if (cgpa >= 2.0) return { label: "Academic Warning",   color: "var(--lp-text-heading)", bg: "#FDF5E0", emoji: "⚠️" };
  return                   { label: "Academic Probation", color: "#C87330", bg: "#FDEAE0", emoji: "🔴" };
}

function getLevelInfo(earnedHours: number): { level: number; label: string } {
  if (earnedHours < 36)  return { level: 1, label: "Freshman"  };
  if (earnedHours < 72)  return { level: 2, label: "Sophomore" };
  if (earnedHours < 108) return { level: 3, label: "Junior"    };
  return                          { level: 4, label: "Senior"    };
}

// ── Hero CGPA arc ring ────────────────────────────────────────────────────────
function CGPARing({ cgpa, color, size = 140 }: { cgpa: number; color: string; size?: number }) {
  const sw   = 11;
  const r    = (size - sw) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - Math.min(cgpa / 4.0, 1));
  const c = size / 2;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Track */}
      <circle cx={c} cy={c} r={r} fill="none" stroke="#C2D0B9" strokeWidth={sw} />
      {/* Progress arc */}
      <circle
        cx={c} cy={c} r={r}
        fill="none" stroke={color} strokeWidth={sw}
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${c} ${c})`}
        style={{ transition: "stroke-dashoffset 0.9s ease" }}
      />
      {/* Center value */}
      <text x={c} y={c - 10} textAnchor="middle" dominantBaseline="middle"
        fill={color} fontSize="22" fontWeight="900" fontFamily="Nunito, sans-serif">
        {cgpa.toFixed(3)}
      </text>
      <text x={c} y={c + 12} textAnchor="middle" dominantBaseline="middle"
        fill="#88734B" fontSize="11" fontWeight="600" fontFamily="Nunito, sans-serif">
        out of 4.0
      </text>
    </svg>
  );
}

// ── Horizontal progress bar ───────────────────────────────────────────────────
function HProgressBar({ value, max }: { value: number; max: number }) {
  const pct = Math.round((value / max) * 100);
  return (
    <div style={{
      width: "100%", height: "7px",
      backgroundColor: "#C2D0B9",
      borderRadius: "9999px",
      overflow: "hidden",
      marginTop: "0.6rem",
    }}>
      <div style={{
        width: `${pct}%`, height: "100%",
        backgroundColor: "#A8BE83",
        borderRadius: "9999px",
        transition: "width 0.9s ease",
      }} />
    </div>
  );
}

// ── Right-column compact card ─────────────────────────────────────────────────
function SideCard({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "var(--lp-bg-card)",
        borderRadius: "1.25rem",
        padding: "1rem 1.25rem",
        boxShadow: "0 3px 14px rgba(79,83,33,0.07)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        transition: "transform 0.18s, box-shadow 0.18s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateX(3px)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 6px 22px rgba(79,83,33,0.11)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateX(0)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 3px 14px rgba(79,83,33,0.07)";
      }}
    >
      {children}
    </div>
  );
}

function SideLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontFamily: "'Nunito', sans-serif",
      color: "var(--lp-text-heading)",
      fontWeight: 700,
      fontSize: "0.68rem",
      textTransform: "uppercase",
      letterSpacing: "0.1em",
      marginBottom: "0.3rem",
    }}>
      {children}
    </p>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export function StatsCards() {
  const isMobile = useIsMobile();
  const { appData } = useAppData();
  const stats = appData!.stats;

  const cgpaColor    = getGPAColor(stats.cgpa);
  const lastSemColor = getGPAColor(stats.lastSemGpa);
  const standing     = getStandingConfig(stats.cgpa);
  const levelInfo    = getLevelInfo(stats.earnedHours);
  const pct          = Math.round((stats.earnedHours / stats.totalHours) * 100);

  const history  = stats.semesterHistory;
  const prevGpa  = history.length >= 2 ? history[history.length - 2].gpa : null;
  const trend    = prevGpa === null ? "neutral"
                 : stats.lastSemGpa > prevGpa ? "up"
                 : stats.lastSemGpa < prevGpa ? "down"
                 : "neutral";
  const trendArrow = trend === "up" ? "↑" : trend === "down" ? "↓" : "↔";
  const trendColor = trend === "up" ? "#9CA35A" : trend === "down" ? "#C87330" : "#88734B";
  const trendBg    = trend === "up" ? "#E8F0DC" : trend === "down" ? "#FDEAE0" : "#EAE3CD";

  return (
    <section id="stats">
      <div style={{ display: "flex", gap: "1rem", alignItems: "stretch", flexWrap: "wrap" }}>

        {/* ── LEFT: Hero card ──────────────────────────────────────────── */}
        <div style={{
          flex: "3",
          minWidth: "280px",
          backgroundColor: "var(--lp-bg-secondary)",
          borderRadius: "1.5rem",
          padding: "1.5rem 1.75rem",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 4px 20px rgba(79,83,33,0.09)",
        }}>

          {/* Welcome row */}
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "0.5rem",
            marginBottom: "1.5rem",
          }}>
            <div>
              <p style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-accent)", fontWeight: 700,
                fontSize: "0.78rem", letterSpacing: "0.1em", textTransform: "uppercase",
              }}>
                Uploaded recently
              </p>
              <h1 style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-dark)", fontWeight: 800, fontSize: "1.5rem", marginTop: "0.2rem",
              }}>
                Welcome 👋
              </h1>
            </div>
            <div style={{
              display: "flex", alignItems: "center", gap: "0.5rem",
              backgroundColor: "var(--lp-bg-primary)", padding: "0.45rem 1rem", borderRadius: "9999px",
            }}>
              <span style={{ fontSize: "1rem" }}>📄</span>
              <span style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.85rem",
              }}>
                {appData!.fileName}
              </span>
            </div>
          </div>

          {/* CGPA ring + standing — fills remaining hero height */}
          <div style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "1rem",
            paddingBottom: "0.5rem",
          }}>
            <CGPARing cgpa={stats.cgpa} color={cgpaColor} size={isMobile ? 110 : 140} />

            {/* Standing badge */}
            <div style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              backgroundColor: standing.bg,
              padding: "0.5rem 1.5rem",
              borderRadius: "9999px",
              boxShadow: `0 2px 10px ${standing.color}30`,
            }}>
              <span style={{ fontSize: "1.1rem" }}>{standing.emoji}</span>
              <span style={{
                fontFamily: "'Nunito', sans-serif",
                color: standing.color, fontWeight: 800, fontSize: "1rem",
              }}>
                {standing.label}
              </span>
            </div>

            <p style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.8rem",
            }}>
              Current CGPA
            </p>
          </div>
        </div>

        {/* ── RIGHT: Three compact cards ────────────────────────────────── */}
        <div style={{
          flex: "2",
          minWidth: "220px",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
        }}>

          {/* Card 1 — Last Semester GPA */}
          <SideCard>
            <SideLabel>Last Semester GPA</SideLabel>
            <p style={{
              fontFamily: "'Nunito', sans-serif",
              color: lastSemColor, fontWeight: 900,
              fontSize: "2.25rem", lineHeight: 1,
            }}>
              {stats.lastSemGpa.toFixed(3)}
            </p>
            <span style={{
              display: "inline-flex", alignItems: "center",
              marginTop: "0.4rem",
              fontFamily: "'Nunito', sans-serif",
              color: trendColor, fontWeight: 700, fontSize: "0.73rem",
              backgroundColor: trendBg,
              padding: "2px 10px", borderRadius: "9999px",
              width: "fit-content",
            }}>
              {trendArrow} vs prev semester
            </span>
          </SideCard>

          {/* Card 2 — Earned Credit Hours */}
          <SideCard>
            <SideLabel>Earned Credit Hours</SideLabel>
            <div style={{ display: "flex", alignItems: "baseline", gap: "0.25rem" }}>
              <span style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-dark)", fontWeight: 900,
                fontSize: "2.25rem", lineHeight: 1,
              }}>
                {stats.earnedHours}
              </span>
              <span style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.9rem",
              }}>
                / {stats.totalHours} hrs
              </span>
            </div>
            <HProgressBar value={stats.earnedHours} max={stats.totalHours} />
            <p style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-accent)", fontWeight: 600,
              fontSize: "0.72rem", marginTop: "0.35rem",
            }}>
              {pct}% to graduation
            </p>
          </SideCard>

          {/* Card 3 — Academic Level */}
          <SideCard>
            <SideLabel>Academic Level</SideLabel>
            <div style={{ display: "flex", alignItems: "center", gap: "0.875rem" }}>
              <div style={{
                width: "48px", height: "48px", minWidth: "48px",
                backgroundColor: "#C2D0B9",
                borderRadius: "50%",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <GraduationCap size={22} color="#4F5321" strokeWidth={2} />
              </div>
              <div>
                <p style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--lp-text-dark)", fontWeight: 900,
                  fontSize: "1.75rem", lineHeight: 1,
                }}>
                  Level {levelInfo.level}
                </p>
                <span style={{
                  display: "inline-block",
                  marginTop: "0.3rem",
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.78rem",
                  backgroundColor: "#C2D0B9",
                  padding: "2px 10px", borderRadius: "9999px",
                }}>
                  {levelInfo.label}
                </span>
              </div>
            </div>
          </SideCard>

        </div>
      </div>
    </section>
  );
}

