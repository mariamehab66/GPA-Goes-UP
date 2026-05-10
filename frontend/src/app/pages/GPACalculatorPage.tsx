import { useState, useEffect } from "react";
import { Plus, X, Calculator } from "lucide-react";
import { useNavigate } from "react-router";
import { DashboardHeader, SIMULATOR_NAV } from "../components/DashboardHeader";
import { Sidebar } from "../components/dashboard/Sidebar";
import { Footer } from "../components/Footer";
import { ChatbotFAB } from "../components/ChatbotFAB";
import { useAppData } from "../context/AppDataContext";
import { useIsMobile } from "../components/ui/use-mobile";

type CalculatorMode = "sgpa" | "cgpa" | null;
type Course = { name: string; grade: string; credits: string };
type Semester = { id: number; name: string; courses: Course[] };

export function GPACalculatorPage() {
  const { appData } = useAppData();
  const navigate = useNavigate();

  useEffect(() => {
    if (!appData) navigate("/", { replace: true });
  }, [appData, navigate]);

  if (!appData) return null;

  return <GPACalculatorContent />;
}

function GPACalculatorContent() {
  const isMobile = useIsMobile();
  const [mode, setMode] = useState<CalculatorMode>(null);
  const [semesters, setSemesters] = useState<Semester[]>([
    {
      id: 1,
      name: "Semester 1",
      courses: [
        { name: "", grade: "", credits: "" },
        { name: "", grade: "", credits: "" },
        { name: "", grade: "", credits: "" },
        { name: "", grade: "", credits: "" },
      ],
    },
  ]);

  const [prevCGPA, setPrevCGPA] = useState("");
  const [prevHours, setPrevHours] = useState("");
  const [lastSemGPA, setLastSemGPA] = useState("");
  const [semHours, setSemHours] = useState("");
  const [cgpaResult, setCgpaResult] = useState<number | null>(null);

  // Grades that count toward GPA (with their quality points)
  const gradePoints: Record<string, number> = {
    "A":   4.00,
    "A-":  3.67,
    "B+":  3.33,
    "B":   3.00,
    "C+":  2.67,
    "C":   2.33,
    "D":   2.00,
    "F":   0.00,
    "Abs": 0.00,
  };

  // All valid grade options (I, W, P exist but are excluded from GPA calculation)
  const allGrades = ["A", "A-", "B+", "B", "C+", "C", "D", "F", "Abs", "I", "W", "P"];

  const resetToModeSelection = () => {
    setMode(null);
    setCgpaResult(null);
  };

  const addSemester = () => {
    const newId = Math.max(...semesters.map((s) => s.id), 0) + 1;
    setSemesters([
      ...semesters,
      {
        id: newId,
        name: `Semester ${newId}`,
        courses: [{ name: "", grade: "", credits: "" }],
      },
    ]);
  };

  const removeSemester = (id: number) => {
    if (semesters.length > 1) {
      setSemesters(semesters.filter((s) => s.id !== id));
    }
  };

  const addCourse = (semId: number) => {
    setSemesters(
      semesters.map((s) =>
        s.id === semId
          ? { ...s, courses: [...s.courses, { name: "", grade: "", credits: "" }] }
          : s
      )
    );
  };

  const removeCourse = (semId: number, courseIdx: number) => {
    setSemesters(
      semesters.map((s) =>
        s.id === semId
          ? { ...s, courses: s.courses.filter((_, i) => i !== courseIdx) }
          : s
      )
    );
  };

  const updateCourse = (semId: number, courseIdx: number, field: keyof Course, value: string) => {
    setSemesters(
      semesters.map((s) =>
        s.id === semId
          ? {
              ...s,
              courses: s.courses.map((c, i) =>
                i === courseIdx ? { ...c, [field]: value } : c
              ),
            }
          : s
      )
    );
  };

  const calculateSemesterGPA = (semester: Semester): number => {
    let totalPoints = 0;
    let totalCredits = 0;

    for (const course of semester.courses) {
      const credits = parseFloat(course.credits);
      const grade = course.grade;

      if (isNaN(credits) || !(grade in gradePoints)) continue;

      totalPoints += credits * gradePoints[grade];
      totalCredits += credits;
    }

    if (totalCredits === 0) return 0;
    return totalPoints / totalCredits;
  };

  const calculateCumulativeGPA = (): number => {
    let totalPoints = 0;
    let totalCredits = 0;

    for (const semester of semesters) {
      for (const course of semester.courses) {
        const credits = parseFloat(course.credits);
        const grade = course.grade;

        if (isNaN(credits) || !(grade in gradePoints)) continue;

        totalPoints += credits * gradePoints[grade];
        totalCredits += credits;
      }
    }

    if (totalCredits === 0) return 0;
    return totalPoints / totalCredits;
  };

  const calculateCGPA = () => {
    const prev = parseFloat(prevCGPA);
    const prevH = parseFloat(prevHours);
    const lastGPA = parseFloat(lastSemGPA);
    const semH = parseFloat(semHours);

    if (isNaN(prev) || isNaN(prevH) || isNaN(lastGPA) || isNaN(semH)) return null;

    const totalPoints = (prev * prevH) + (lastGPA * semH);
    const totalHours = prevH + semH;

    if (totalHours === 0) return null;
    return totalPoints / totalHours;
  };

  const handleCalculateCGPA = () => {
    const result = calculateCGPA();
    if (result !== null) setCgpaResult(result);
  };

  const cumulativeGPA = calculateCumulativeGPA();

  // Build chatbot context string from current calculator state
  const chatContext = (() => {
    if (mode === null) {
      return "User is on the GPA Calculator. They have not chosen a mode yet (SGPA or CGPA).";
    }
    if (mode === "cgpa") {
      const base =
        `User is on the GPA Calculator — Cumulative GPA (CGPA) mode.\n` +
        `Inputs: Previous CGPA ${prevCGPA || "—"}, Previous Hours ${prevHours || "—"}, ` +
        `Last Semester GPA ${lastSemGPA || "—"}, Semester Hours ${semHours || "—"}.`;
      return cgpaResult !== null
        ? `${base}\nCalculated new CGPA: ${cgpaResult.toFixed(2)}.`
        : `${base}\nNo result calculated yet.`;
    }
    // SGPA mode
    const hasData = semesters.some(s =>
      s.courses.some(c => c.grade && c.credits && !isNaN(parseFloat(c.credits)))
    );
    if (!hasData) {
      return "User is on the GPA Calculator — Semester GPA (SGPA) mode. No course data entered yet.";
    }
    const semLines = semesters
      .map(sem => {
        const valid = sem.courses.filter(
          c => c.grade && c.credits && !isNaN(parseFloat(c.credits)) && c.grade in gradePoints
        );
        if (valid.length === 0) return null;
        const gpa     = calculateSemesterGPA(sem);
        const courses = valid.map(c => `${c.name || "Unnamed"} (${c.grade}, ${c.credits} cr)`).join(", ");
        return `  ${sem.name}: GPA ${gpa.toFixed(2)} — ${courses}`;
      })
      .filter(Boolean)
      .join("\n");
    return [
      "User is on the GPA Calculator — Semester GPA (SGPA) mode.",
      `${semesters.length} semester(s) entered. Cumulative GPA: ${cumulativeGPA.toFixed(2)}.`,
      semLines ? `Details:\n${semLines}` : "",
    ].filter(Boolean).join("\n");
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
        <Sidebar activePage="calculator" />

        <main
          style={{
            flex: 1,
            minWidth: 0,
            padding: "1.75rem 2rem 3rem",
            backgroundColor: "var(--lp-bg-card)",
            display: "flex",
            flexDirection: "column",
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
              Calculate your grades
            </p>
            <h1
              style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-dark)",
                fontWeight: 800,
                fontSize: "1.75rem",
              }}
            >
              GPA Calculator
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
              Calculate your Semester GPA or update your Cumulative GPA.
            </p>
          </div>

          {/* Divider */}
          <div
            style={{
              height: "1px",
              backgroundColor: "var(--lp-bg-secondary)",
              borderRadius: "9999px",
              margin: "1.25rem 0 1.75rem",
            }}
          />

          {/* â”€â”€ Mode Selection â”€â”€ */}
          {mode === null && (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: "100%", maxWidth: "700px" }}>
              <div style={{ backgroundColor: "var(--lp-bg-secondary)", borderRadius: "1.75rem", padding: "2.5rem", boxShadow: "0 6px 32px rgba(79,83,33,0.10)" }}>
                <h2 style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 800, fontSize: "1.3rem", marginBottom: "1.5rem", textAlign: "center" }}>
                  Which Calculator?
                </h2>
                <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
                  <button
                    onClick={() => setMode("sgpa")}
                    style={{ flex: 1, minWidth: "200px", backgroundColor: "#A8BE83", color: "#fff", fontFamily: "'Nunito', sans-serif", fontWeight: 800, fontSize: "1.1rem", padding: "1.5rem", borderRadius: "1.25rem", border: "none", cursor: "pointer", transition: "transform 0.18s, box-shadow 0.18s", boxShadow: "0 4px 18px rgba(168,190,131,0.45)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.03)"; e.currentTarget.style.boxShadow = "0 8px 28px rgba(168,190,131,0.55)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 4px 18px rgba(168,190,131,0.45)"; }}
                  >
                    📊 Semester GPA (SGPA)
                  </button>
                  <button
                    onClick={() => setMode("cgpa")}
                    style={{ flex: 1, minWidth: "200px", backgroundcolor: "var(--lp-text-dark)", color: "#fff", fontFamily: "'Nunito', sans-serif", fontWeight: 800, fontSize: "1.1rem", padding: "1.5rem", borderRadius: "1.25rem", border: "none", cursor: "pointer", transition: "transform 0.18s, box-shadow 0.18s", boxShadow: "0 4px 18px rgba(79,83,33,0.45)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.03)"; e.currentTarget.style.boxShadow = "0 8px 28px rgba(79,83,33,0.55)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 4px 18px rgba(79,83,33,0.45)"; }}
                  >
                    🎯 Cumulative GPA (CGPA)
                  </button>
                </div>
              </div>
            </div>
            </div>
          )}

          {/* â”€â”€ SGPA Calculator â”€â”€ */}
          {mode === "sgpa" && (
            <>
              <div style={{ marginBottom: "1.5rem" }}>
                <button
                  onClick={resetToModeSelection}
                  style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-primary)", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.85rem", padding: "0.5rem 1rem", borderRadius: "9999px", border: "none", cursor: "pointer" }}
                >
                  ← Change Mode
                </button>
              </div>

              <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap", alignItems: "flex-start" }}>
                {/* Left side - Semesters */}
                <div style={{ flex: "1 1 600px", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                  {semesters.map((semester) => {
                    const semGPA = calculateSemesterGPA(semester);
                    return (
                      <div
                        key={semester.id}
                        style={{ backgroundColor: "#fff", borderRadius: "1.5rem", padding: "1.75rem", boxShadow: "0 4px 24px rgba(79,83,33,0.08)", border: "2px solid #EAE3CD" }}
                      >
                        {/* Semester Header */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
                          <h2 style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 800, fontSize: "1.25rem", margin: 0 }}>
                            {semester.name}
                          </h2>
                          {semesters.length > 1 && (
                            <button
                              onClick={() => removeSemester(semester.id)}
                              style={{ backgroundColor: "transparent", border: "none", cursor: "pointer", padding: "0.25rem", display: "flex", alignItems: "center" }}
                            >
                              <X size={20} color="#88734B" strokeWidth={2} />
                            </button>
                          )}
                        </div>

                        {/* Course Headers */}
                        {!isMobile && (
                        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 40px", gap: "0.75rem", marginBottom: "0.75rem" }}>
                          <div style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.8rem" }}>Course name (optional)</div>
                          <div style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.8rem" }}>Grade</div>
                          <div style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.8rem" }}>Credits</div>
                          <div />
                        </div>
                        )}

                        {/* Courses */}
                        {semester.courses.map((course, idx) => (
                          <div
                            key={idx}
                            style={isMobile
                              ? { display: "flex", flexWrap: "wrap" as const, gap: "0.5rem", marginBottom: "0.75rem" }
                              : { display: "grid", gridTemplateColumns: "2fr 1fr 1fr 40px", gap: "0.75rem", marginBottom: "0.75rem" }
                            }
                          >
                            <input
                              type="text"
                              value={course.name}
                              onChange={(e) => updateCourse(semester.id, idx, "name", e.target.value)}
                              placeholder="Course name (optional)"
                              style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-card)", color: "var(--lp-text-dark)", fontWeight: 500, fontSize: "0.9rem", padding: "0.6rem 0.85rem", borderRadius: "0.5rem", border: "2px solid #EAE3CD", outline: "none", ...(isMobile && { flex: "1 1 100%" }) }}
                            />
                            <select
                              value={course.grade}
                              onChange={(e) => updateCourse(semester.id, idx, "grade", e.target.value)}
                              style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-card)", color: "var(--lp-text-dark)", fontWeight: 500, fontSize: "0.9rem", padding: "0.6rem 0.85rem", borderRadius: "0.5rem", border: "2px solid #EAE3CD", outline: "none", ...(isMobile && { flex: 1, minWidth: 0 }) }}
                            >
                              <option value="">Grade</option>
                              {allGrades.map((g) => (
                                <option key={g} value={g}>{g}</option>
                              ))}
                            </select>
                            <input
                              type="number"
                              value={course.credits}
                              onChange={(e) => updateCourse(semester.id, idx, "credits", e.target.value)}
                              placeholder="Credits"
                              min="0"
                              step="1"
                              style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-card)", color: "var(--lp-text-dark)", fontWeight: 500, fontSize: "0.9rem", padding: "0.6rem 0.85rem", borderRadius: "0.5rem", border: "2px solid #EAE3CD", outline: "none", ...(isMobile && { flex: 1, minWidth: 0 }) }}
                            />
                            <button
                              onClick={() => removeCourse(semester.id, idx)}
                              disabled={semester.courses.length === 1}
                              style={{ backgroundColor: "transparent", border: "none", cursor: semester.courses.length === 1 ? "not-allowed" : "pointer", padding: "0.25rem", display: "flex", alignItems: "center", justifyContent: "center", opacity: semester.courses.length === 1 ? 0.3 : 1 }}
                            >
                              <X size={18} color="#88734B" strokeWidth={2} />
                            </button>
                          </div>
                        ))}

                        {/* Semester GPA & Add Course */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1.25rem", paddingTop: "1rem", borderTop: "1px solid #EAE3CD" }}>
                          <div style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "1rem" }}>
                            {semester.name} GPA: <span style={{ color: "#A8BE83", fontSize: "1.1rem" }}>{semGPA.toFixed(2)}</span>
                          </div>
                          <button
                            onClick={() => addCourse(semester.id)}
                            style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "#C2D0B9", color: "var(--lp-text-dark)", fontWeight: 600, fontSize: "0.85rem", padding: "0.5rem 1rem", borderRadius: "9999px", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem", transition: "background-color 0.2s" }}
                            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "#A8BE83"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "#C2D0B9"; }}
                          >
                            <Plus size={16} strokeWidth={2.5} /> Add Course
                          </button>
                        </div>
                      </div>
                    );
                  })}

                  {/* Add Semester Button */}
                  <button
                    onClick={addSemester}
                    style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-secondary)", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.95rem", padding: "0.85rem 1.5rem", borderRadius: "9999px", border: "2px solid #DEDBD2", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.5rem", alignSelf: "flex-start", transition: "background-color 0.2s, border-color 0.2s" }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "#DEDBD2"; e.currentTarget.style.borderColor = "#C2D0B9"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "#EAE3CD"; e.currentTarget.style.borderColor = "#DEDBD2"; }}
                  >
                    <Plus size={18} strokeWidth={2.5} /> Add Semester
                  </button>
                </div>

                {/* Right side - Cumulative GPA Circle */}
                <div style={{ flex: "0 0 280px", position: "sticky", top: "2rem" }}>
                  <div style={{ backgroundColor: "#fff", borderRadius: "1.5rem", padding: "2rem", boxShadow: "0 4px 24px rgba(79,83,33,0.08)", border: "2px solid #EAE3CD", display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ position: "relative", width: "200px", height: "200px", marginBottom: "1rem" }}>
                      <svg width="200" height="200" style={{ transform: "rotate(-90deg)" }}>
                        <circle cx="100" cy="100" r="85" fill="none" stroke="#EAE3CD" strokeWidth="12" />
                        <circle
                          cx="100"
                          cy="100"
                          r="85"
                          fill="none"
                          stroke="#A8BE83"
                          strokeWidth="12"
                          strokeDasharray={`${(cumulativeGPA / 4.0) * 534} 534`}
                          strokeLinecap="round"
                          style={{ transition: "stroke-dasharray 0.8s ease" }}
                        />
                      </svg>
                      <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", textAlign: "center" }}>
                        <div style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 900, fontSize: "3rem", lineHeight: 1 }}>
                          {cumulativeGPA.toFixed(2)}
                        </div>
                        <div style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.85rem", marginTop: "0.25rem" }}>
                          Cumulative GPA
                        </div>
                      </div>
                    </div>
                    <div style={{ width: "100%", display: "flex", justifyContent: "space-between", paddingTop: "0.5rem" }}>
                      <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.8rem" }}>0.0</span>
                      <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.8rem" }}>4.0</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* â”€â”€ CGPA Calculator â”€â”€ */}
          {mode === "cgpa" && (
            <div style={{ maxWidth: "700px" }}>
              <div style={{ backgroundColor: "var(--lp-bg-secondary)", borderRadius: "1.75rem", padding: "2rem", boxShadow: "0 6px 32px rgba(79,83,33,0.10)", marginBottom: "2rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
                  <div>
                    <h2 style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 800, fontSize: "1.25rem", marginBottom: "0.2rem" }}>
                      Calculate Cumulative GPA
                    </h2>
                    <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 500, fontSize: "0.9rem" }}>
                      Enter your academic history to calculate your new CGPA
                    </p>
                  </div>
                  <button
                    onClick={resetToModeSelection}
                    style={{ fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-primary)", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.85rem", padding: "0.5rem 1rem", borderRadius: "9999px", border: "none", cursor: "pointer" }}
                  >
                    ← Change Mode
                  </button>
                </div>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
                  <div style={{ flex: 1, minWidth: "200px" }}>
                    <label style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.82rem", display: "block", marginBottom: "0.4rem" }}>
                      📊 Previous CGPA
                    </label>
                    <input
                      type="number"
                      value={prevCGPA}
                      onChange={(e) => setPrevCGPA(e.target.value)}
                      placeholder="e.g. 3.24"
                      min="0"
                      max="4"
                      step="0.01"
                      style={{ width: "100%", fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-primary)", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "1.05rem", padding: "0.65rem 1rem", borderRadius: "0.875rem", border: "2px solid transparent", outline: "none", boxSizing: "border-box" }}
                    />
                  </div>
                  <div style={{ flex: 1, minWidth: "200px" }}>
                    <label style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.82rem", display: "block", marginBottom: "0.4rem" }}>
                      📚 Previous Hours
                    </label>
                    <input
                      type="number"
                      value={prevHours}
                      onChange={(e) => setPrevHours(e.target.value)}
                      placeholder="e.g. 68"
                      min="0"
                      step="1"
                      style={{ width: "100%", fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-primary)", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "1.05rem", padding: "0.65rem 1rem", borderRadius: "0.875rem", border: "2px solid transparent", outline: "none", boxSizing: "border-box" }}
                    />
                  </div>
                </div>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
                  <div style={{ flex: 1, minWidth: "200px" }}>
                    <label style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.82rem", display: "block", marginBottom: "0.4rem" }}>
                      🎯 Last Semester GPA
                    </label>
                    <input
                      type="number"
                      value={lastSemGPA}
                      onChange={(e) => setLastSemGPA(e.target.value)}
                      placeholder="e.g. 3.50"
                      min="0"
                      max="4"
                      step="0.01"
                      style={{ width: "100%", fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-primary)", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "1.05rem", padding: "0.65rem 1rem", borderRadius: "0.875rem", border: "2px solid transparent", outline: "none", boxSizing: "border-box" }}
                    />
                  </div>
                  <div style={{ flex: 1, minWidth: "200px" }}>
                    <label style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.82rem", display: "block", marginBottom: "0.4rem" }}>
                      ⏱️ Semester Hours
                    </label>
                    <input
                      type="number"
                      value={semHours}
                      onChange={(e) => setSemHours(e.target.value)}
                      placeholder="e.g. 18"
                      min="0"
                      step="1"
                      style={{ width: "100%", fontFamily: "'Nunito', sans-serif", backgroundColor: "var(--lp-bg-primary)", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "1.05rem", padding: "0.65rem 1rem", borderRadius: "0.875rem", border: "2px solid transparent", outline: "none", boxSizing: "border-box" }}
                    />
                  </div>
                </div>

                <button
                  onClick={handleCalculateCGPA}
                  style={{ fontFamily: "'Nunito', sans-serif", width: "100%", backgroundcolor: "var(--lp-text-dark)", color: "#fff", fontWeight: 800, fontSize: "1.05rem", padding: "0.875rem", borderRadius: "1rem", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.6rem", transition: "transform 0.18s, box-shadow 0.18s", boxShadow: "0 4px 18px rgba(79,83,33,0.45)" }}
                  onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.025)"; e.currentTarget.style.boxShadow = "0 8px 28px rgba(79,83,33,0.55)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 4px 18px rgba(79,83,33,0.45)"; }}
                >
                  <Calculator size={18} strokeWidth={2.5} /> Calculate CGPA
                </button>
              </div>

              {cgpaResult !== null && (
                <div style={{ backgroundColor: "#F0F6EA", borderRadius: "1.75rem", padding: "2rem", boxShadow: "0 6px 32px rgba(79,83,33,0.10)", border: "3px solid #4F5321" }}>
                  <div style={{ textAlign: "center" }}>
                    <h3 style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 800, fontSize: "1.3rem", marginBottom: "1.5rem" }}>
                      Your New Cumulative GPA 🎉
                    </h3>
                    <div style={{ display: "inline-block", backgroundcolor: "var(--lp-text-dark)", color: "#fff", fontFamily: "'Nunito', sans-serif", fontWeight: 900, fontSize: "3.5rem", padding: "1rem 2.5rem", borderRadius: "1.5rem", boxShadow: "0 8px 24px rgba(79,83,33,0.45)" }}>
                      {cgpaResult.toFixed(2)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      <Footer />
      <ChatbotFAB pageContext={chatContext} />
    </div>
  );
}



