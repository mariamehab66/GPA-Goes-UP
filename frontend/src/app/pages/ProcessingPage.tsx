import { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import { useAppData } from "../context/AppDataContext";
import type { AppData } from "../context/AppDataContext";
import { apiUrl } from "@/lib/api";
import ThemeToggle from "../components/ThemeToggle";

const STATUS_MESSAGES = [
  "Parsing Transcript...",
  "Analyzing Academic Record...",
  "Generating Recommendations...",
];

const MIN_DISPLAY_MS = 4500;

// ── API helpers ───────────────────────────────────────────────────────────────

async function fetchStudentId(): Promise<number> {
  const res = await fetch(apiUrl("/api/session/student-id"));
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? "No active session. Please upload your transcript first.");
  }
  const { student_id } = await res.json();
  return student_id as number;
}

type ApiError = { code: string };

async function fetchRecommendations(studentId: number, targetSemester: string): Promise<Omit<AppData, 'fileName'>> {
  const res = await fetch(apiUrl("/api/recommend"), {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ student_id: studentId, target_semester: targetSemester }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw { code: body.error ?? "system-error" } satisfies ApiError;
  }
  const data = await res.json();

  return {
    stats: {
      studentId:       data.student_id,
      cgpa:            data.student_stats.cgpa,
      earnedHours:     data.student_stats.earned_hours,
      totalHours:      data.student_stats.total_hours,
      lastSemGpa:      data.student_stats.last_sem_gpa,
      semesterHistory: data.student_stats.semester_history,
    },
    topRecommended:        data.top_recommended,
    alternativeCourses:    data.alternative_courses,
    academicStatus:        data.academic_status,
    maxAllowedHours:       data.max_allowed_hours,
    warnings:              data.warnings,
    totalRecommendedHours: data.total_recommended_hours,
    allEligibleCourses:    data.all_eligible_courses ?? [],
  };
}

// ── Component ─────────────────────────────────────────────────────────────────

export function ProcessingPage() {
  const navigate    = useNavigate();
  const location    = useLocation();
  const { setAppData } = useAppData();

  const locationState  = location.state as { semester?: string; fileName?: string } | null;
  const targetSemester = locationState?.semester ?? "fall";
  const fileName       = locationState?.fileName ?? "transcript.pdf";

  const [statusIndex, setStatusIndex] = useState(0);
  const [progress,    setProgress]    = useState(0);
  const [visible,     setVisible]     = useState(true);

  // Cycle status labels every 1.5 s with a brief fade
  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setStatusIndex((i) => (i + 1) % STATUS_MESSAGES.length);
        setVisible(true);
      }, 220);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  // Smooth progress bar 0 → 100 over MIN_DISPLAY_MS
  useEffect(() => {
    const startTime    = performance.now();
    const fillDuration = MIN_DISPLAY_MS - 100;
    let raf: number;

    const tick = (now: number) => {
      const elapsed = now - startTime;
      setProgress(Math.min((elapsed / fillDuration) * 100, 100));
      if (elapsed < fillDuration) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  // API call — runs in parallel with the minimum display timer.
  // Both must complete before navigating so the animation always plays fully.
  const ranRef = useRef(false);
  useEffect(() => {
    if (ranRef.current) return;
    ranRef.current = true;

    const apiCall = async () => {
      const studentId = await fetchStudentId();
      return fetchRecommendations(studentId, targetSemester);
    };

    const minWait = new Promise<void>((res) => setTimeout(res, MIN_DISPLAY_MS));

    const ERROR_PAGE_CODES = new Set([
      "graduated",
      "invalid-sequence",
      "semester-completed",
      "system-error",
      "upload-failed",
      "timeout",
    ]);

    Promise.all([apiCall(), minWait])
      .then(([data]) => {
        setAppData({ ...data, fileName });
        navigate("/dashboard", { replace: true });
      })
      .catch((err: unknown) => {
        const code = (err as ApiError).code ?? "system-error";
        navigate(
          `/error?type=${ERROR_PAGE_CODES.has(code) ? code : "system-error"}`,
          { replace: true },
        );
      });
  }, []);

  // ── Processing animation ───────────────────────────────────────────────────
  return (
    <div style={{
      fontFamily: "'Nunito', sans-serif",
      backgroundColor: "var(--lp-bg-card)",
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "2rem",
    }}>
      <div style={{ position: "fixed", top: "1rem", right: "1rem", zIndex: 50 }}>
        <ThemeToggle />
      </div>
      <div style={{
        backgroundColor: "var(--lp-bg-secondary)",
        borderRadius: "1.75rem",
        padding: "3rem 3.5rem",
        maxWidth: "460px",
        width: "100%",
        textAlign: "center",
        boxShadow: "0 6px 32px rgba(79,83,33,0.10)",
      }}>
        {/* Animated icon bubble */}
        <div style={{
          width: "80px", height: "80px",
          borderRadius: "50%",
          backgroundColor: "#C2D0B9",
          display: "flex", alignItems: "center", justifyContent: "center",
          margin: "0 auto 1.5rem",
          fontSize: "2.25rem",
          boxShadow: "0 4px 20px rgba(168,190,131,0.30)",
        }}>
          📈
        </div>

        <h1 style={{
          fontFamily: "'Nunito', sans-serif",
          color: "var(--lp-text-dark)", fontWeight: 800, fontSize: "1.55rem",
          marginBottom: "0.3rem",
        }}>
          Analyzing Your Record
        </h1>

        <p style={{
          fontFamily: "'Nunito', sans-serif",
          color: "var(--lp-text-heading)", fontWeight: 500, fontSize: "0.9rem",
          marginBottom: "2rem",
        }}>
          This will only take a moment.
        </p>

        {/* Progress bar */}
        <div style={{
          height: "10px", backgroundColor: "var(--lp-bg-primary)",
          borderRadius: "9999px", overflow: "hidden",
          marginBottom: "0.6rem",
        }}>
          <div style={{
            height: "100%", width: `${progress}%`,
            backgroundcolor: "var(--lp-footer-subtext)",
            borderRadius: "9999px",
            boxShadow: "0 0 8px rgba(168,190,131,0.50)",
            transition: "width 0.08s linear",
          }} />
        </div>

        <p style={{
          fontFamily: "'Nunito', sans-serif",
          color: "var(--lp-text-accent)", fontWeight: 700, fontSize: "0.78rem",
          marginBottom: "1.5rem", letterSpacing: "0.04em",
        }}>
          {Math.round(progress)}%
        </p>

        {/* Pulsing status text */}
        <p style={{
          fontFamily: "'Nunito', sans-serif",
          color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "1rem",
          minHeight: "1.5rem", marginBottom: "2.25rem",
          opacity: visible ? 1 : 0,
          transition: "opacity 0.22s ease",
        }}>
          {STATUS_MESSAGES[statusIndex]}
        </p>

        <p style={{
          fontFamily: "'Nunito', sans-serif",
          color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.88rem",
          lineHeight: 1.65,
        }}>
          Mapping your journey to success...
        </p>

        {/* Dot indicators */}
        <div style={{
          display: "flex", justifyContent: "center",
          gap: "0.4rem", marginTop: "1.75rem",
        }}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{
              width: "7px", height: "7px",
              borderRadius: "50%",
              backgroundcolor: "var(--lp-footer-subtext)",
              opacity: statusIndex === i ? 1 : 0.35,
              transition: "opacity 0.3s ease",
            }} />
          ))}
        </div>
      </div>
    </div>
  );
}
