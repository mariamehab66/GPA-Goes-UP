import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import ThemeToggle from "../components/ThemeToggle";
import confetti from "canvas-confetti";
import {
  FileX,
  CloudOff,
  AlertCircle,
  FileWarning,
  Clock,
  ShieldAlert,
  Home,
  RefreshCw,
  CalendarX,
  GraduationCap,
} from "lucide-react";

const CONFETTI_COLORS = ["#A8BE83", "#9CA35A", "#F2C27F", "#C2D0B9", "#4F5321", "#EAE3CD", "#C87330"];

// ── Error type catalogue ──────────────────────────────────────────────────────

export type UploadErrorType =
  | "wrong-file"
  | "upload-failed"
  | "system-error"
  | "file-too-large"
  | "corrupted-file"
  | "timeout"
  | "invalid-sequence"
  | "semester-completed"
  | "graduated";

type Severity = "critical" | "warning" | "celebration";

type ErrorConfig = {
  severity: Severity;
  icon: React.ElementType;
  badge: string;
  title: string;
  message: string;
  tip: string;
  fireConfetti?: true;
  primaryLabel?: string;
  secondaryLabel?: string;
  secondaryRoute?: string;
};

const ERROR_CONFIGS: Record<UploadErrorType, ErrorConfig> = {
  "wrong-file": {
    severity: "critical",
    icon: FileX,
    badge: "Wrong File Type",
    title: "Oops! That's not a PDF.",
    message:
      "Please upload your academic record in PDF format. We can only read .pdf files exported directly from your university",
    tip: "Tip: From your Academic Advisor, ask to send your academic record to you as a PDF attachment, then save that attachment and upload it here.",
  },
  "upload-failed": {
    severity: "warning",
    icon: CloudOff,
    badge: "Upload Failed",
    title: "Your File Didn't Make It Through.",
    message:
      "We couldn't receive your file — this is usually a brief network hiccup. Check your internet connection and try uploading again.",
    tip: "Tip: A stable Wi-Fi connection, or use a mobile data connection work best",
  },
  "system-error": {
    severity: "critical",
    icon: AlertCircle,
    badge: "System Error",
    title: "Something Went Wrong on Our End.",
    message:
      "Our system hit an unexpected error while processing your record. This is not your fault — please try again in a moment. If it keeps happening, try refreshing the page first.",
    tip: "Tip: Errors like this are usually temporary. Waiting 30 seconds before retrying often helps.",
  },
  "file-too-large": {
    severity: "critical",
    icon: FileWarning,
    badge: "File Too Large",
    title: "Your PDF is Too Large to Upload.",
    message:
      "We accept PDF files up to 10 MB. Your transcript appears to exceed that limit. Please compress it before trying again.",
    tip: "Tip: Free tools like ilovepdf.com can compress your PDF in seconds without losing quality.",
  },
  "corrupted-file": {
    severity: "critical",
    icon: ShieldAlert,
    badge: "Unreadable File",
    title: "We Couldn't Read Your PDF.",
    message:
      "Your file appears to be corrupted or password-protected. Please download a fresh copy of your transcript from your student portal and try again.",
    tip: "Tip: Make sure the PDF is not encrypted or password-locked before uploading.",
  },
  timeout: {
    severity: "warning",
    icon: Clock,
    badge: "Processing Timed Out",
    title: "The Analysis Took Too Long.",
    message:
      "We weren't able to finish analyzing your transcript in time. This can happen with very large files or a slow connection. Please try uploading again.",
    tip: "Tip: A faster, stable connection significantly speeds up the analysis.",
  },
  "invalid-sequence": {
    severity: "critical",
    icon: CalendarX,
    badge: "Invalid Semester Order",
    title: "That Semester Doesn't Follow Your Progress.",
    message:
      "The semester you selected breaks the standard academic sequence. Each semester must logically follow the one before it — you cannot skip ahead or select one out of order.",
    tip: "Tip: The correct flow is Fall → Spring, Spring → Fall or Summer, and Summer → Fall. Please go back and select the semester that naturally comes after your last completed one.",
  },
  "semester-completed": {
    severity: "warning",
    icon: GraduationCap,
    badge: "Semester Complete!",
    title: "You've Finished Every Subject This Semester!",
    message:
      "Incredible work — you have already completed all available subjects for this semester. There is nothing left to plan here, and every semester you finish brings you one step closer to the finish line. Graduation is getting closer!",
    tip: "Tip: Head back and select your next upcoming semester to keep that momentum going. You are on the right track — keep it up!",
  },
  graduated: {
    severity: "celebration",
    icon: GraduationCap,
    badge: "Mission Accomplished!",
    title: "You Did It — You've Graduated! 🎓",
    message:
      "You have completed all your degree requirements. Every early morning, every late night, every exam — it all led here. The finish line is behind you, and your future is wide open. We are so proud of you!",
    tip: "Your academic journey with GPA Goes UP is complete. Head to your dashboard to look back at everything you achieved.",
    fireConfetti: true,
    primaryLabel: "Back to Home",
    secondaryLabel: "View My Dashboard",
    secondaryRoute: "/dashboard",
  },
};

// ── Severity-driven visual tokens ─────────────────────────────────────────────

const SEVERITY_STYLES: Record<Severity, {
  iconBg: string;
  iconColor: string;
  badgeBg: string;
  badgeColor: string;
  borderAccent: string;
  tipBg: string;
}> = {
  critical: {
    iconBg: "#FEF0E6",
    iconColor: "#C87330",
    badgeBg: "#FEF0E6",
    badgeColor: "#C87330",
    borderAccent: "#C87330",
    tipBg: "#FEF8F0",
  },
  warning: {
    iconBg: "#EAE3CD",
    iconcolor: "var(--lp-text-heading)",
    badgeBg: "#DEDBD2",
    badgecolor: "var(--lp-text-heading)",
    borderAccent: "#A8BE83",
    tipBg: "#F4F1E8",
  },
  celebration: {
    iconBg: "#C2D0B9",
    iconcolor: "var(--lp-text-dark)",
    badgeBg: "#C2D0B9",
    badgecolor: "var(--lp-text-dark)",
    borderAccent: "#A8BE83",
    tipBg: "#EDF3E6",
  },
};

// ── Props ─────────────────────────────────────────────────────────────────────

type Props = {
  /** Pass directly when embedding as a component; omit to read from ?type= URL param. */
  type?: UploadErrorType;
};

// ── Page ──────────────────────────────────────────────────────────────────────

export function UploadErrorPage({ type: typeProp }: Props) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Resolve error type: prop → URL param → safe default
  const rawType = typeProp ?? (searchParams.get("type") as UploadErrorType | null) ?? "system-error";
  const errorType: UploadErrorType =
    rawType in ERROR_CONFIGS ? rawType : "system-error";

  const cfg = ERROR_CONFIGS[errorType];
  const sv = SEVERITY_STYLES[cfg.severity];
  const Icon = cfg.icon;

  useEffect(() => {
    if (!cfg.fireConfetti) return;
    confetti({ particleCount: 120, spread: 80, origin: { x: 0.5, y: 0.55 }, colors: CONFETTI_COLORS, scalar: 1.1 });
    setTimeout(() => confetti({ particleCount: 70, angle: 65,  spread: 58, origin: { x: 0, y: 0.6 }, colors: CONFETTI_COLORS, scalar: 1.0 }), 280);
    setTimeout(() => confetti({ particleCount: 70, angle: 115, spread: 58, origin: { x: 1, y: 0.6 }, colors: CONFETTI_COLORS, scalar: 1.0 }), 560);
    setTimeout(() => confetti({ particleCount: 50, spread: 120, startVelocity: 20, gravity: 0.6, origin: { x: 0.5, y: 0 }, colors: CONFETTI_COLORS, scalar: 0.85 }), 1100);
  }, []);

  return (
    <div
      style={{
        fontFamily: "'Nunito', sans-serif",
        backgroundColor: "var(--lp-bg-card)",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
      }}
    >
      <div style={{ position: "fixed", top: "1rem", right: "1rem", zIndex: 50 }}>
        <ThemeToggle />
      </div>

      {/* ── Central card ───────────────────────────────────────────────────── */}
      <div
        style={{
          backgroundColor: "var(--lp-bg-secondary)",
          borderRadius: "1.75rem",
          padding: "2.75rem 3rem",
          maxWidth: "500px",
          width: "100%",
          boxShadow: "0 6px 32px rgba(79,83,33,0.10)",
          borderTop: `4px solid ${sv.borderAccent}`,
        }}
      >
        {/* Icon bubble + badge row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            marginBottom: "1.75rem",
          }}
        >
          <div
            style={{
              width: "64px",
              height: "64px",
              minWidth: "64px",
              borderRadius: "50%",
              backgroundColor: sv.iconBg,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: `0 4px 16px ${sv.borderAccent}28`,
            }}
          >
            <Icon size={28} color={sv.iconColor} strokeWidth={2} />
          </div>

          <span
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: sv.badgeColor,
              fontWeight: 700,
              fontSize: "0.72rem",
              backgroundColor: sv.badgeBg,
              padding: "4px 12px",
              borderRadius: "9999px",
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              border: `1px solid ${sv.borderAccent}44`,
            }}
          >
            {cfg.badge}
          </span>
        </div>

        {/* Title */}
        <h1
          style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-dark)",
            fontWeight: 800,
            fontSize: "1.45rem",
            lineHeight: 1.35,
            marginBottom: "0.75rem",
          }}
        >
          {cfg.title}
        </h1>

        {/* Message */}
        <p
          style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-heading)",
            fontWeight: 500,
            fontSize: "0.95rem",
            lineHeight: 1.7,
            marginBottom: "1.5rem",
          }}
        >
          {cfg.message}
        </p>

        {/* Tip box */}
        <div
          style={{
            backgroundColor: sv.tipBg,
            borderRadius: "1rem",
            padding: "0.9rem 1.1rem",
            borderLeft: `3px solid ${sv.borderAccent}`,
            marginBottom: "2rem",
          }}
        >
          <p
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-heading)",
              fontWeight: 600,
              fontSize: "0.85rem",
              lineHeight: 1.6,
            }}
          >
            {cfg.tip}
          </p>
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {/* Primary — back to home */}
          <button
            onClick={() => navigate("/")}
            style={{
              fontFamily: "'Nunito', sans-serif",
              backgroundcolor: "var(--lp-footer-subtext)",
              color: "#ffffff",
              fontWeight: 800,
              fontSize: "1rem",
              padding: "0.875rem 1.5rem",
              borderRadius: "9999px",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.55rem",
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
            <Home size={16} strokeWidth={2.5} />
            {cfg.primaryLabel ?? "Back to Home to Try Again"}
          </button>

          {/* Secondary — retry or custom route */}
          <button
            onClick={() => navigate(cfg.secondaryRoute ?? "/")}
            style={{
              fontFamily: "'Nunito', sans-serif",
              backgroundColor: "transparent",
              color: "var(--lp-text-heading)",
              fontWeight: 700,
              fontSize: "0.92rem",
              padding: "0.75rem 1.5rem",
              borderRadius: "9999px",
              border: "2px solid #88734B",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.55rem",
              transition: "background-color 0.15s, color 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "#88734B";
              e.currentTarget.style.color = "#fff";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
              e.currentTarget.style.color = "#88734B";
            }}
          >
            <RefreshCw size={15} strokeWidth={2.5} />
            {cfg.secondaryLabel ?? "Try Uploading Again"}
          </button>
        </div>
      </div>

      {/* Reassurance note below card */}
      <p
        style={{
          fontFamily: "'Nunito', sans-serif",
          color: "var(--lp-text-accent)",
          fontWeight: 600,
          fontSize: "0.82rem",
          marginTop: "1.5rem",
          textAlign: "center",
        }}
      >
        Your data is safe — nothing was saved.
      </p>
    </div>
  );
}
