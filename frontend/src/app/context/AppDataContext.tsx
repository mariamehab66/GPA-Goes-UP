import { createContext, useContext, useState, useEffect, useRef } from "react";
import { type CourseData } from "../data/courses";
import { apiUrl } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

export type SemesterHistory = {
  sem: string;
  gpa: number;
};

export type StudentStats = {
  studentId: number;
  cgpa: number;
  earnedHours: number;
  totalHours: number;
  lastSemGpa: number;
  semesterHistory: SemesterHistory[];
};

export type EligibleCourse = {
  Code: string;
  Course_Name: string;
  Credit_Hours: number;
  Level?: number;
  Semester?: string;
  Type?: string;
  Is_elective: boolean;
  Is_practical?: boolean;
  is_failed?: boolean;
};

export type CourseRecommendation = {
  Code: string;
  Course_Name: string;
  Credit_Hours: number;
  Level?: number;
  Semester?: string;
  Type?: string;
  Is_elective: boolean;
  Is_practical?: boolean;
  mandatory?: boolean;
  note?: string;
  predicted_grade_bucket: "Excellent" | "Good" | "Average" | "Low" | "Fail";
  predicted_grade_range: string;
  grade_probabilities: {
    Excellent: number;
    Good: number;
    Average: number;
    Low: number;
    Fail: number;
  };
};

export type AppData = {
  fileName: string;
  stats: StudentStats;
  topRecommended: CourseRecommendation[];
  alternativeCourses: CourseRecommendation[];
  academicStatus: string;
  maxAllowedHours: number;
  warnings: string[];
  totalRecommendedHours: number;
  allEligibleCourses: EligibleCourse[];
};

// ── Shared course mapper (used by GPASimulator and RecommendationsPage) ──────
export function toCourseData(c: CourseRecommendation): CourseData {
  return {
    id:                  c.Code,
    name:                c.Course_Name,
    code:                c.Code,
    creditHours:         Number(c.Credit_Hours),
    mandatory:           !c.Is_elective,
    note:                c.note,
    grade_probabilities: c.grade_probabilities,
  };
}

// ── Context ───────────────────────────────────────────────────────────────────

type AppDataContextValue = {
  appData: AppData | null;
  setAppData: (data: AppData) => void;
};

const AppDataContext = createContext<AppDataContextValue>({
  appData: null,
  setAppData: () => {},
});

// ── Provider ──────────────────────────────────────────────────────────────────

export function AppDataProvider({ children }: { children: React.ReactNode }) {
  const [appData, setAppData] = useState<AppData | null>(null);

  // Keep a ref so the beforeunload handler always sees the latest value
  // without needing to re-register the event listener.
  const hasDataRef = useRef(false);
  useEffect(() => {
    hasDataRef.current = appData !== null;
  }, [appData]);

  // Purge student data from DB when the user closes/refreshes the tab.
  // sendBeacon is used because fetch() is cancelled during page unload.
  useEffect(() => {
    const handleUnload = () => {
      if (hasDataRef.current) {
        navigator.sendBeacon(apiUrl("/api/session/purge"));
      }
    };
    window.addEventListener("beforeunload", handleUnload);
    return () => window.removeEventListener("beforeunload", handleUnload);
  }, []);

  return (
    <AppDataContext.Provider value={{ appData, setAppData }}>
      {children}
    </AppDataContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAppData() {
  return useContext(AppDataContext);
}
