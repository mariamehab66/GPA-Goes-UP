import { useState, useRef } from "react";
import {
  Sparkles, Target, TrendingUp, ChevronRight, Trophy,
  AlertCircle, Zap, Loader2,
} from "lucide-react";
import { apiUrl } from "@/lib/api";
import { DashboardHeader, SIMULATOR_NAV } from "../components/DashboardHeader";
import { Sidebar } from "../components/dashboard/Sidebar";
import { AboutSection } from "../components/AboutSection";
import { Footer } from "../components/Footer";
import { ChatbotFAB } from "../components/ChatbotFAB";

// â”€â”€ Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

type PlannerPhase = "idle" | "loading" | "success" | "impossible";

type SemesterType = "regular" | "summer";

type Milestone = {
  semNum: number;
  type: SemesterType;
  creditHours: number;
  requiredSemGPA: number;
  cumulativeGPA: number;
  isLast: boolean;
  statusLabel: string;
  maxAllowedHours: number;
  warnings: string[];
  emoji: string;
};

// â”€â”€ Counter animation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function animateCounter(
  start: number,
  end: number,
  duration: number,
  decimals: number,
  onUpdate: (v: string) => void,
  onDone?: () => void
) {
  const startTime = performance.now();
  const tick = (now: number) => {
    const t = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    const val = start + (end - start) * eased;
    onUpdate(val.toFixed(decimals));
    if (t < 1) requestAnimationFrame(tick);
    else onDone?.();
  };
  requestAnimationFrame(tick);
}

// â”€â”€ Status badge derived from Rule Engine warnings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function getStatusBadge(
  statusLabel: string,
  warnings: string[]
): { text: string; color: string; bg: string } | null {
  if (statusLabel === "probation")
    return { text: "⚠️ Probation — 12 hr cap", color: "#C87330", bg: "#FEF0E6" };
  if (statusLabel === "delayed")
    return { text: "⚡ Delayed — 16 hr cap", color: "var(--lp-text-heading)", bg: "#FEF8EE" };
  if (statusLabel === "summer")
    return { text: "☀️ Summer Retake Window", color: "var(--lp-text-heading)", bg: "#FEF8EE" };

  const hasSenior = warnings.some((w) => w.toLowerCase().includes("senior"));
  if (hasSenior)
    return { text: "🎓 Senior Exception +3 hrs", color: "var(--lp-text-dark)", bg: "#E8F0DC" };

  const hasBonus = warnings.some((w) => w.toLowerCase().includes("bonus"));
  if (hasBonus)
    return { text: "✨ GPA Bonus +3 hrs", color: "var(--lp-text-dark)", bg: "#E8F0DC" };

  return null;
}

// â”€â”€ Input Field â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function InputField({
  label, value, onChange, placeholder, min, max, step, icon, highlight,
}: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder: string; min?: number; max?: number; step?: number;
  icon: string; highlight?: boolean;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", flex: 1, minWidth: "160px" }}>
      <label style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.82rem", letterSpacing: "0.03em" }}>
        {icon} {label}
      </label>
      <input
        type="number" value={value} onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder} min={min} max={max} step={step}
        style={{
          fontFamily: "'Nunito', sans-serif",
          backgroundColor: highlight ? "var(--lp-bg-card)" : "var(--lp-bg-primary)",
          color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "1.05rem",
          padding: "0.65rem 1rem", borderRadius: "0.875rem",
          border: highlight ? "2px solid #A8BE83" : "2px solid transparent",
          outline: "none", width: "100%",
          transition: "border-color 0.25s, background-color 0.25s, box-shadow 0.25s",
          boxShadow: highlight ? "0 0 0 4px rgba(168,190,131,0.18)" : "none",
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = "#A8BE83";
          e.currentTarget.style.backgroundColor = "#fff";
          e.currentTarget.style.boxShadow = "0 0 0 4px rgba(168,190,131,0.18)";
        }}
        onBlur={(e) => {
          if (!highlight) {
            e.currentTarget.style.borderColor = "transparent";
            e.currentTarget.style.backgroundColor = "var(--lp-bg-primary)";
            e.currentTarget.style.boxShadow = "none";
          }
        }}
      />
    </div>
  );
}

// â”€â”€ GPA Track Bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function GPATrackBar({ current, target }: { current: number; target: number }) {
  const currentPct = (current / 4.0) * 100;
  const targetPct  = (target  / 4.0) * 100;
  return (
    <div style={{ marginBottom: "1.75rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
        <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.82rem" }}>
          Current CGPA: {current.toFixed(3)}
        </span>
        <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 800, fontSize: "0.82rem" }}>
          Target: {target.toFixed(3)} 🎯
        </span>
      </div>
      <div style={{ height: "12px", backgroundColor: "var(--lp-bg-primary)", borderRadius: "9999px", position: "relative", overflow: "visible" }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${currentPct}%`, backgroundColor: "#C2D0B9", borderRadius: "9999px", transition: "width 0.8s ease" }} />
        <div style={{ position: "absolute", left: `${targetPct}%`, top: "-4px", transform: "translateX(-50%)", width: "4px", height: "20px", backgroundColor: "#A8BE83", borderRadius: "9999px" }} />
        <div style={{ position: "absolute", left: `${targetPct}%`, top: "-22px", transform: "translateX(-50%)", backgroundColor: "#A8BE83", color: "#fff", fontFamily: "'Nunito', sans-serif", fontWeight: 800, fontSize: "0.65rem", padding: "1px 6px", borderRadius: "9999px", whiteSpace: "nowrap" }}>
          {target.toFixed(3)}
        </div>
      </div>
    </div>
  );
}

// â”€â”€ Milestone Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function MilestoneCard({
  milestone, index, totalSemesters, visible,
}: {
  milestone: Milestone; index: number; totalSemesters: number; visible: boolean;
}) {
  const isSummer  = milestone.type === "summer";
  const stairStep = Math.min(index, 3);
  const stairOffset = stairStep * 22;
  const progress  = (index + 1) / totalSemesters;

  // Colour scheme: summer = amber, last regular = dark green, regular = sage
  const borderColor = isSummer
    ? "#F2C27F"
    : milestone.isLast ? "#4F5321" : "#A8BE83";
  const bgColor = isSummer
    ? "#FEF8EE"
    : milestone.isLast ? "#F0F6EA" : "var(--lp-bg-card)";
  const badgeBg = isSummer
    ? "#F2C27F"
    : milestone.isLast ? "#4F5321" : "#C2D0B9";
  const badgeFg = milestone.isLast && !isSummer ? "#fff" : "#4F5321";
  const dotBg   = isSummer ? "#F2C27F" : milestone.isLast ? "#4F5321" : "#A8BE83";

  const statusBadge = getStatusBadge(milestone.statusLabel, milestone.warnings);

  return (
    <div
      style={{
        marginLeft: `${stairOffset}px`,
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(20px)",
        transition: `opacity 0.4s ease ${index * 0.1}s, transform 0.4s ease ${index * 0.1}s`,
        display: "flex", alignItems: "flex-start", gap: "1rem", position: "relative",
      }}
    >
      {/* Connector line */}
      {!milestone.isLast && (
        <div style={{ position: "absolute", left: "23px", top: "48px", width: "2px", height: "calc(100% + 0.75rem)", background: isSummer ? "linear-gradient(180deg,#F2C27F 0%,#EAE3CD 100%)" : "linear-gradient(180deg,#A8BE83 0%,#C2D0B9 100%)", borderRadius: "9999px" }} />
      )}

      {/* Step badge */}
      <div style={{ width: "48px", height: "48px", minWidth: "48px", borderRadius: "50%", backgroundColor: dotBg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", boxShadow: `0 4px 16px ${borderColor}44`, zIndex: 1, position: "relative", flexShrink: 0 }}>
        <span style={{ fontSize: "1.15rem", lineHeight: 1 }}>{milestone.emoji}</span>
        <span style={{ fontFamily: "'Nunito', sans-serif", color: "#fff", fontWeight: 800, fontSize: "0.55rem", letterSpacing: "0.04em" }}>
          {isSummer ? "SUM" : `SEM ${milestone.semNum}`}
        </span>
      </div>

      {/* Card body */}
      <div
        style={{ flex: 1, backgroundColor: bgColor, borderRadius: "1.25rem", borderLeft: `4px solid ${borderColor}`, padding: "1rem 1.25rem", boxShadow: "0 4px 20px rgba(79,83,33,0.08)", marginBottom: "0.75rem", transition: "transform 0.18s, box-shadow 0.18s" }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.transform = "translateX(4px)"; (e.currentTarget as HTMLDivElement).style.boxShadow = "0 8px 28px rgba(79,83,33,0.14)"; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.transform = "translateX(0)"; (e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 20px rgba(79,83,33,0.08)"; }}
      >
        {/* Header row */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.5rem" }}>
          <span style={{ fontFamily: "'Nunito', sans-serif", color: milestone.isLast && !isSummer ? "var(--lp-text-dark)" : "var(--lp-text-heading)", fontWeight: 800, fontSize: "1rem" }}>
            {isSummer
              ? `☀️ Summer Retake`
              : `Semester ${milestone.semNum}${milestone.isLast ? " — Final Push 🎓" : ""}`}
          </span>
          <span style={{ fontFamily: "'Nunito', sans-serif", color: badgeFg, fontWeight: 700, fontSize: "0.72rem", backgroundColor: badgeBg, padding: "2px 10px", borderRadius: "9999px" }}>
            {milestone.creditHours} credit hrs
          </span>
        </div>

        {/* Rule Engine status badge */}
        {statusBadge && (
          <div style={{ marginBottom: "0.5rem" }}>
            <span style={{ fontFamily: "'Nunito', sans-serif", color: statusBadge.color, fontWeight: 700, fontSize: "0.7rem", backgroundColor: statusBadge.bg, padding: "2px 9px", borderRadius: "9999px", border: `1px solid ${statusBadge.color}33` }}>
              {statusBadge.text}
            </span>
          </div>
        )}

        {/* Main instruction */}
        <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 600, fontSize: "0.92rem", lineHeight: 1.55 }}>
          {isSummer
            ? <>Retake <strong style={{ color: "var(--lp-text-heading)" }}>{milestone.creditHours} credit hour{milestone.creditHours !== 1 ? "s" : ""}</strong> of eligible failed courses. Aim for a semester GPA of <strong style={{ color: borderColor, fontSize: "1.05rem" }}>{milestone.requiredSemGPA.toFixed(3)}</strong>.</>
            : <>Enroll in <strong style={{ color: "var(--lp-text-heading)" }}>{milestone.creditHours} credit hours</strong>{" "}<span style={{ color: "var(--lp-text-accent)", fontSize: "0.8rem" }}>(Rule Engine max: {milestone.maxAllowedHours})</span>. Aim for a semester GPA of <strong style={{ color: borderColor, fontSize: "1.05rem" }}>{milestone.requiredSemGPA.toFixed(3)}</strong>.</>
          }
        </p>

        {/* Cumulative GPA after milestone */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.6rem" }}>
          <TrendingUp size={14} color={borderColor} strokeWidth={2.5} />
          <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.8rem" }}>
            Cumulative GPA after this semester:{" "}
            <strong style={{ color: borderColor }}>{milestone.cumulativeGPA.toFixed(3)}</strong>
          </span>
        </div>

        {/* Progress bar */}
        <div style={{ marginTop: "0.65rem", height: "5px", backgroundColor: "var(--lp-bg-secondary)", borderRadius: "9999px", overflow: "hidden" }}>
          <div style={{ width: `${progress * 100}%`, height: "100%", backgroundColor: borderColor, borderRadius: "9999px", transition: "width 0.8s ease" }} />
        </div>
        <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-accent)", fontWeight: 600, fontSize: "0.7rem", marginTop: "0.25rem", display: "block" }}>
          {Math.round(progress * 100)}% of journey complete
        </span>
      </div>
    </div>
  );
}

// â”€â”€ Impossible Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function ImpossibleCard({ maxGPA, onAimForMax }: { maxGPA: number; onAimForMax: () => void }) {
  return (
    <div style={{ backgroundColor: "#FFF7E6", border: "2px solid #F2C27F", borderRadius: "1.5rem", padding: "1.75rem", boxShadow: "0 6px 28px rgba(200,115,48,0.12)", display: "flex", flexDirection: "column", gap: "1rem", alignItems: "flex-start" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <div style={{ width: "48px", height: "48px", borderRadius: "50%", backgroundColor: "#F2C27F", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <AlertCircle size={24} color="#88734B" strokeWidth={2} />
        </div>
        <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.75rem", backgroundColor: "#F2C27F", padding: "3px 10px", borderRadius: "9999px", letterSpacing: "0.05em", textTransform: "uppercase" }}>
          Out of reach
        </span>
      </div>
      <div>
        <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "1.1rem", lineHeight: 1.5, marginBottom: "0.5rem" }}>
          Target is mathematically out of reach, but don't stop! 💪
        </p>
        <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 500, fontSize: "0.95rem", lineHeight: 1.65 }}>
          Even if you score a perfect <strong>4.0</strong> every semester from now on, the highest CGPA you can achieve is{" "}
          <strong style={{ color: "#C87330", fontSize: "1.15rem" }}>{maxGPA.toFixed(3)}</strong>. That's still a fantastic goal — let's plan for that instead!
        </p>
      </div>
      <button
        onClick={onAimForMax}
        style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "#C87330", color: "#fff", fontWeight: 800, fontSize: "0.95rem", padding: "0.7rem 1.75rem", borderRadius: "9999px", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.5rem", transition: "transform 0.18s, box-shadow 0.18s", boxShadow: "0 4px 16px rgba(200,115,48,0.35)" }}
        onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.04)"; e.currentTarget.style.boxShadow = "0 8px 24px rgba(200,115,48,0.45)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 4px 16px rgba(200,115,48,0.35)"; }}
      >
        <Zap size={16} strokeWidth={2.5} />
        Aim for Max ({maxGPA.toFixed(3)})
      </button>
    </div>
  );
}

// â”€â”€ Main Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export function PlannerPage() {
  const [cgpa,         setCgpa]         = useState("");
  const [earnedHours,  setEarnedHours]  = useState("");
  const [hoursForGrad, setHoursForGrad] = useState("");
  const [targetGPA,    setTargetGPA]    = useState("");

  const [phase,        setPhase]        = useState<PlannerPhase>("idle");
  const [milestones,   setMilestones]   = useState<Milestone[]>([]);
  const [maxGPA,       setMaxGPA]       = useState(0);
  const [requiredAvg,  setRequiredAvg]  = useState(0);
  const [cardsVisible, setCardsVisible] = useState(false);

  const [autoFilling,       setAutoFilling]       = useState(false);
  const [highlightedFields, setHighlightedFields] = useState(false);
  const [apiError,          setApiError]          = useState<string | null>(null);

  const resultsRef = useRef<HTMLDivElement>(null);

  // â”€â”€ Auto-fill from database â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const handleAutoFill = async () => {
    if (autoFilling || phase === "loading") return;
    setAutoFilling(true);
    setApiError(null);

    try {
      const res  = await fetch(apiUrl("/api/planner/autofill"));
      const data = await res.json();

      if (!res.ok) {
        setApiError(data.error ?? "Could not load your academic data.");
        setAutoFilling(false);
        return;
      }

      const dur = 900;
      setCgpa("0.00");
      setEarnedHours("0");
      setHoursForGrad("0");
      setHighlightedFields(true);

      animateCounter(0, data.cgpa,         dur, 2, setCgpa);
      animateCounter(0, data.earnedHours,  dur, 0, setEarnedHours);
      animateCounter(0, data.hoursForGrad, dur, 0, setHoursForGrad, () => {
        setAutoFilling(false);
      });
    } catch {
      setApiError("Network error — is the Flask server running?");
      setAutoFilling(false);
    }
  };

  // â”€â”€ Run the Rule Engine planner via backend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const runPlan = async (overrideTarget?: number) => {
    const c = parseFloat(cgpa);
    const e = parseFloat(earnedHours);
    const g = parseFloat(hoursForGrad);
    const t = overrideTarget ?? parseFloat(targetGPA);

    if (isNaN(c) || isNaN(e) || isNaN(g) || isNaN(t)) return;
    if (c < 0 || c > 4 || t < 0 || t > 4 || e < 0 || g <= 0 || e >= g) return;

    setPhase("loading");
    setApiError(null);

    try {
      const res  = await fetch(apiUrl("/api/planner/calculate"), {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ cgpa: c, earnedHours: e, hoursForGrad: g, targetGpa: t }),
      });
      const data = await res.json();

      if (!res.ok) {
        setApiError(data.error ?? "Calculation failed.");
        setPhase("idle");
        return;
      }

      if (data.phase === "impossible") {
        setMaxGPA(data.max_gpa);
        setPhase("impossible");
        setMilestones([]);
      } else {
        setMilestones(data.milestones);
        setRequiredAvg(data.required_avg);
        setPhase("success");
        setCardsVisible(false);
        setTimeout(() => setCardsVisible(true), 80);
      }

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 150);
    } catch {
      setApiError("Network error — is the Flask server running?");
      setPhase("idle");
    }
  };

  const handlePlan = () => runPlan();

  // â”€â”€ Aim for Max â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const handleAimForMax = () => {
    const currentTarget = parseFloat(targetGPA) || 0;
    animateCounter(currentTarget, maxGPA, 700, 2, setTargetGPA, () => {
      runPlan(maxGPA);
    });
  };

  // Build chatbot context string from current planner state
  const plannerContext = (() => {
    const inputs =
      `Current CGPA: ${cgpa || "—"}, Earned Hours: ${earnedHours || "—"}, ` +
      `Hours for Graduation: ${hoursForGrad || "—"}, Target CGPA: ${targetGPA || "—"}`;
    if (phase === "idle" || phase === "loading") {
      return `User is on the Target GPA Planner. Inputs: ${inputs}. No plan calculated yet.`;
    }
    if (phase === "impossible") {
      return (
        `User is on the Target GPA Planner.\n` +
        `Inputs: ${inputs}.\n` +
        `Result: Target CGPA ${targetGPA} is mathematically IMPOSSIBLE.\n` +
        `Even scoring 4.0 every semester, the maximum achievable CGPA is ${maxGPA.toFixed(3)}.`
      );
    }
    // success
    const msLines = milestones
      .map(m => {
        const label  = m.type === "summer" ? "Summer retake" : `Semester ${m.semNum}`;
        const status = m.statusLabel && m.statusLabel !== "normal" ? ` [${m.statusLabel}]` : "";
        return `  ${label}: ${m.creditHours} cr hrs, target GPA ${m.requiredSemGPA.toFixed(3)}${status} → CGPA after: ${m.cumulativeGPA.toFixed(3)}`;
      })
      .join("\n");
    return [
      "User is on the Target GPA Planner.",
      `Inputs: ${inputs}.`,
      `Plan is ACHIEVABLE in ${milestones.length} semester(s).`,
      `Required consistent semester GPA: ${requiredAvg.toFixed(3)}.`,
      `Roadmap:\n${msLines}`,
    ].join("\n");
  })();

  const canSubmit =
    cgpa !== "" && earnedHours !== "" && hoursForGrad !== "" && targetGPA !== "" &&
    !isNaN(parseFloat(cgpa)) && !isNaN(parseFloat(earnedHours)) &&
    !isNaN(parseFloat(hoursForGrad)) && !isNaN(parseFloat(targetGPA)) &&
    phase !== "loading";

  return (
    <div style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-card)", minHeight: "100vh", overflowX: "hidden" }}>
      <DashboardHeader navItems={SIMULATOR_NAV} />

      <div style={{ display: "flex", alignItems: "flex-start" }}>
        <Sidebar activePage="planner" />

        <main style={{ flex: 1, minWidth: 0, padding: "1.75rem 2rem 3rem", backgroundColor: "var(--lp-bg-card)" }}>

          {/* Page intro */}
          <div style={{ marginBottom: "1.5rem" }}>
            <h1 style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 800, fontSize: "1.75rem" }}>
              Target GPA Planner 🎯
            </h1>
            <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 500, fontSize: "0.95rem", marginTop: "0.35rem" }}>
              Enter your academic record, set your dream GPA, and we'll map out exactly what you need each semester — respecting your real credit limits.
            </p>
          </div>

          {/* â”€â”€ Input Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
          <div style={{ backgroundColor: "var(--lp-bg-secondary)", borderRadius: "1.75rem", padding: "2rem", boxShadow: "0 6px 32px rgba(79,83,33,0.10)", marginBottom: "2rem", maxWidth: "720px" }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
              <div>
                <h2 style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 800, fontSize: "1.25rem", marginBottom: "0.2rem" }}>
                  Set Your Academic Goal
                </h2>
                <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 500, fontSize: "0.9rem" }}>
                  Where do you want to see your GPA go next?
                </p>
              </div>

              {/* Auto-fill button */}
              <button
                onClick={handleAutoFill}
                disabled={autoFilling || phase === "loading"}
                style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: autoFilling ? "#C2D0B9" : "var(--lp-bg-primary)", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.82rem", padding: "0.55rem 1.1rem", borderRadius: "9999px", border: "none", cursor: autoFilling ? "default" : "pointer", display: "flex", alignItems: "center", gap: "0.45rem", transition: "background-color 0.2s, transform 0.15s", flexShrink: 0, boxShadow: "0 2px 8px rgba(79,83,33,0.1)" }}
                onMouseEnter={(e) => { if (!autoFilling) { e.currentTarget.style.backgroundColor = "#C2D0B9"; e.currentTarget.style.transform = "scale(1.03)"; } }}
                onMouseLeave={(e) => { if (!autoFilling) { e.currentTarget.style.backgroundColor = "var(--lp-bg-primary)"; e.currentTarget.style.transform = "scale(1)"; } }}
              >
                {autoFilling
                  ? <><Loader2 size={14} strokeWidth={2.5} style={{ animation: "spin 1s linear infinite" }} /> Filling...</>
                  : <><Sparkles size={14} strokeWidth={2.5} color="#88734B" /> Auto-Fill from Record</>
                }
              </button>
            </div>

            {/* API error banner */}
            {apiError && (
              <div style={{ backgroundColor: "#FEF0E6", border: "1.5px solid #F2C27F", borderRadius: "0.875rem", padding: "0.65rem 1rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <AlertCircle size={15} color="#C87330" strokeWidth={2} />
                <span style={{ fontFamily: "'Nunito', sans-serif", color: "#C87330", fontWeight: 600, fontSize: "0.82rem" }}>{apiError}</span>
              </div>
            )}

            {/* Input grid — row 1 */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
              <InputField label="Current CGPA"        value={cgpa}         onChange={setCgpa}         placeholder="e.g. 3.24" min={0} max={4} step={0.01} icon="📊" highlight={highlightedFields && cgpa !== ""} />
              <InputField label="Earned Credit Hours" value={earnedHours}  onChange={setEarnedHours}  placeholder="e.g. 68"   min={0} step={1}             icon="📚" highlight={highlightedFields && earnedHours !== ""} />
            </div>
            {/* Input grid — row 2 */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
              <InputField label="Total Hours for Graduation" value={hoursForGrad} onChange={setHoursForGrad} placeholder="e.g. 140" min={1} step={1}             icon="🎓" highlight={highlightedFields && hoursForGrad !== ""} />
              <InputField label="Target CGPA"               value={targetGPA}    onChange={setTargetGPA}    placeholder="e.g. 3.70" min={0} max={4} step={0.01} icon="🎯" highlight={false} />
            </div>

            {/* Plan button */}
            <button
              onClick={handlePlan}
              disabled={!canSubmit}
              style={{ fontFamily: "'Nunito', sans-serif", width: "100%", backgroundColor: canSubmit ? "#A8BE83" : "#C2D0B9", color: "#fff", fontWeight: 800, fontSize: "1.05rem", padding: "0.875rem", borderRadius: "1rem", border: "none", cursor: canSubmit ? "pointer" : "default", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.6rem", transition: "transform 0.18s, box-shadow 0.18s, background-color 0.2s", boxShadow: canSubmit ? "0 4px 18px rgba(168,190,131,0.45)" : "none" }}
              onMouseEnter={(e) => { if (canSubmit) { e.currentTarget.style.transform = "scale(1.025)"; e.currentTarget.style.boxShadow = "0 8px 28px rgba(168,190,131,0.55)"; } }}
              onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = canSubmit ? "0 4px 18px rgba(168,190,131,0.45)" : "none"; }}
            >
              {phase === "loading"
                ? <><Loader2 size={18} strokeWidth={2.5} style={{ animation: "spin 1s linear infinite" }} /> Calculating your plan...</>
                : <><Target size={18} strokeWidth={2.5} /> Plan My Goal <ChevronRight size={18} strokeWidth={2.5} /></>
              }
            </button>
          </div>

          {/* â”€â”€ Results â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
          {(phase === "success" || phase === "impossible") && (
            <div ref={resultsRef}>
              <div style={{ height: "1px", backgroundColor: "var(--lp-bg-secondary)", borderRadius: "9999px", marginBottom: "1.75rem" }} />

              {/* Results header */}
              <div style={{ marginBottom: "1.5rem" }}>
                <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-accent)", fontWeight: 700, fontSize: "0.78rem", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "0.25rem" }}>
                  {phase === "success" ? "Your Roadmap" : "Smart Fallback"}
                </p>
                <h2 style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 800, fontSize: "1.35rem" }}>
                  {phase === "success"
                    ? `${milestones.length} Semester${milestones.length !== 1 ? "s" : ""} to Reach Your Goal 📈`
                    : "Let's Find Your Best Path 💡"}
                </h2>
                {phase === "success" && requiredAvg > 0 && (
                  <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.85rem", marginTop: "0.3rem" }}>
                    Consistent target semester GPA:{" "}
                    <strong style={{ color: "var(--lp-text-dark)" }}>{requiredAvg.toFixed(3)}</strong>
                    {" "}— credit limits set per semester by the Rule Engine.
                  </p>
                )}
              </div>

              {/* GPA track bar */}
              {phase === "success" && milestones.length > 0 && (
                <GPATrackBar current={parseFloat(cgpa)} target={parseFloat(targetGPA)} />
              )}

              {/* Staircase */}
              {phase === "success" && (
                <div style={{ maxWidth: "680px", display: "flex", flexDirection: "column" }}>
                  {milestones.map((m, i) => (
                    <MilestoneCard key={`${m.type}-${m.semNum}`} milestone={m} index={i} totalSemesters={milestones.length} visible={cardsVisible} />
                  ))}

                  {/* Graduation banner */}
                  <div
                    style={{ opacity: cardsVisible ? 1 : 0, transform: cardsVisible ? "translateY(0)" : "translateY(20px)", transition: `opacity 0.4s ease ${milestones.length * 0.1 + 0.1}s, transform 0.4s ease ${milestones.length * 0.1 + 0.1}s`, marginTop: "0.5rem", marginLeft: `${Math.min(milestones.length, 4) * 22}px`, backgroundcolor: "var(--lp-text-dark)", borderRadius: "1.25rem", padding: "1.25rem 1.5rem", display: "flex", alignItems: "center", gap: "1rem", boxShadow: "0 6px 24px rgba(79,83,33,0.2)" }}
                  >
                    <Trophy size={28} color="#F2C27F" strokeWidth={2} />
                    <div>
                      <p style={{ fontFamily: "'Nunito', sans-serif", color: "#F2C27F", fontWeight: 800, fontSize: "1rem" }}>
                        Graduation Day — CGPA: {parseFloat(targetGPA).toFixed(3)} 🎓
                      </p>
                      <p style={{ fontFamily: "'Nunito', sans-serif", color: "#C2D0B9", fontWeight: 500, fontSize: "0.82rem", marginTop: "0.2rem" }}>
                        Stay consistent and this is exactly where you'll be.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Impossible fallback */}
              {phase === "impossible" && (
                <div style={{ maxWidth: "620px" }}>
                  <ImpossibleCard maxGPA={maxGPA} onAimForMax={handleAimForMax} />
                </div>
              )}
            </div>
          )}

        </main>
      </div>

      <AboutSection />
      <Footer />
      <ChatbotFAB pageContext={plannerContext} />

      {/* Spinner keyframe */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}




