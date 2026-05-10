import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { Search } from "lucide-react";
import { DashboardHeader, SIMULATOR_NAV } from "../components/DashboardHeader";
import { Sidebar } from "../components/dashboard/Sidebar";
import { Footer } from "../components/Footer";
import { ChatbotFAB } from "../components/ChatbotFAB";
import { useAppData, type EligibleCourse } from "../context/AppDataContext";

// â”€â”€ Eligible Course Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function EligibleCourseCard({ course }: { course: EligibleCourse }) {
  const borderColor = course.Is_elective ? "#F2C27F" : "#A8BE83";
  const semLabel = course.Semester
    ? course.Semester.charAt(0).toUpperCase() + course.Semester.slice(1).toLowerCase()
    : "";

  return (
    <div
      style={{
        backgroundColor: "var(--lp-bg-card)",
        borderRadius: "1rem",
        borderLeft: `4px solid ${borderColor}`,
        padding: "0.875rem 1.1rem",
        boxShadow: "0 2px 10px rgba(79,83,33,0.06)",
        transition: "transform 0.18s, box-shadow 0.18s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateX(3px)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 16px rgba(79,83,33,0.11)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateX(0)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 2px 10px rgba(79,83,33,0.06)";
      }}
    >
      {/* Code + Level row */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "0.35rem",
      }}>
        <span style={{
          fontFamily: "'Nunito', sans-serif",
          fontSize: "0.72rem", fontWeight: 700,
          color: "var(--lp-text-heading)", backgroundColor: "var(--lp-bg-secondary)",
          padding: "2px 9px", borderRadius: "9999px",
        }}>
          {course.Code}
        </span>
        {course.Level !== undefined && (
          <span style={{
            fontFamily: "'Nunito', sans-serif",
            fontSize: "0.68rem", fontWeight: 700,
            color: "var(--lp-text-dark)", backgroundColor: "#C2D0B9",
            padding: "2px 9px", borderRadius: "9999px",
          }}>
            Level {course.Level}
          </span>
        )}
      </div>

      {/* Course name */}
      <p style={{
        fontFamily: "'Nunito', sans-serif",
        color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.92rem",
        margin: "0 0 0.6rem", lineHeight: 1.35,
      }}>
        {course.Course_Name}
      </p>

      {/* Tags row */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
        <span style={{
          fontFamily: "'Nunito', sans-serif",
          fontSize: "0.65rem", fontWeight: 700,
          color: course.Is_elective ? "#7A5C00" : "#4F5321",
          backgroundColor: course.Is_elective ? "#FDF0D0" : "#E8F0DC",
          padding: "2px 8px", borderRadius: "9999px",
        }}>
          {course.Is_elective ? "Elective" : "Required"}
        </span>

        {semLabel && (
          <span style={{
            fontFamily: "'Nunito', sans-serif",
            fontSize: "0.65rem", fontWeight: 700,
            color: "var(--lp-text-heading)", backgroundColor: "var(--lp-bg-secondary)",
            padding: "2px 8px", borderRadius: "9999px",
          }}>
            {semLabel}
          </span>
        )}

        <span style={{
          fontFamily: "'Nunito', sans-serif",
          fontSize: "0.65rem", fontWeight: 700,
          color: "var(--lp-text-heading)", backgroundColor: "var(--lp-bg-secondary)",
          padding: "2px 8px", borderRadius: "9999px",
        }}>
          {course.Credit_Hours} cr
        </span>

        {course.Is_practical && (
          <span style={{
            fontFamily: "'Nunito', sans-serif",
            fontSize: "0.65rem", fontWeight: 700,
            color: "#5C5C5C", backgroundColor: "#DEDDDA",
            padding: "2px 8px", borderRadius: "9999px",
          }}>
            Practical
          </span>
        )}
      </div>
    </div>
  );
}

// â”€â”€ Courses list with filters â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function CourseList({ courses }: { courses: EligibleCourse[] }) {
  const [search,          setSearch]          = useState("");
  const [levelFilter,    setLevelFilter]    = useState<number | "all">("all");
  const [typeFilter,     setTypeFilter]     = useState<"all" | "mandatory" | "elective">("all");
  const [semesterFilter, setSemesterFilter] = useState<"all" | "fall" | "spring" | "summer">("all");

  const levels = [
    ...new Set(
      courses
        .map((c) => c.Level)
        .filter((l): l is number => l !== undefined),
    ),
  ].sort((a, b) => a - b);

  const filtered = courses.filter((c) => {
    const q = search.toLowerCase();
    const matchSearch =
      !search ||
      c.Course_Name.toLowerCase().includes(q) ||
      c.Code.toLowerCase().includes(q);
    const matchLevel =
      levelFilter === "all" || c.Level === levelFilter;
    const matchType =
      typeFilter === "all" ||
      (typeFilter === "elective" ? c.Is_elective : !c.Is_elective);
    const normSem = c.Semester?.toLowerCase() ?? "";
    const matchSemester =
      semesterFilter === "all" ||
      (semesterFilter === "summer"
        ? c.is_failed === true
        : normSem === semesterFilter || normSem === "both");
    return matchSearch && matchLevel && matchType && matchSemester;
  });

  return (
    <>
      {/* Filter bar */}
      <div style={{
        display: "flex",
        gap: "0.75rem",
        flexWrap: "wrap",
        alignItems: "center",
        padding: "0.875rem 1.1rem",
        backgroundColor: "var(--lp-bg-secondary)",
        borderRadius: "1rem",
        marginBottom: "1.5rem",
      }}>
        {/* Search */}
        <div style={{ position: "relative", flex: "1 1 200px" }}>
          <Search
            size={13}
            style={{
              position: "absolute", left: "10px",
              top: "50%", transform: "translateY(-50%)",
              color: "var(--lp-text-heading)", pointerEvents: "none",
            }}
          />
          <input
            type="text"
            placeholder="Search by name or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              fontFamily: "'Nunito', sans-serif",
              width: "100%",
              padding: "0.45rem 0.75rem 0.45rem 2rem",
              borderRadius: "0.75rem",
              border: "1.5px solid #C2D0B9",
              backgroundColor: "var(--lp-bg-card)",
              fontSize: "0.83rem",
              color: "var(--lp-text-dark)",
              outline: "none",
              boxSizing: "border-box",
            }}
          />
        </div>

        {/* Level filter */}
        <select
          value={String(levelFilter)}
          onChange={(e) =>
            setLevelFilter(e.target.value === "all" ? "all" : Number(e.target.value))
          }
          style={{
            fontFamily: "'Nunito', sans-serif",
            padding: "0.45rem 0.9rem",
            borderRadius: "0.75rem",
            border: "1.5px solid #C2D0B9",
            backgroundColor: "var(--lp-bg-card)",
            fontSize: "0.83rem",
            color: "var(--lp-text-dark)",
            cursor: "pointer",
            outline: "none",
          }}
        >
          <option value="all">All Levels</option>
          {levels.map((l) => (
            <option key={l} value={l}>Level {l}</option>
          ))}
        </select>

        {/* Type filter */}
        <select
          value={typeFilter}
          onChange={(e) =>
            setTypeFilter(e.target.value as "all" | "mandatory" | "elective")
          }
          style={{
            fontFamily: "'Nunito', sans-serif",
            padding: "0.45rem 0.9rem",
            borderRadius: "0.75rem",
            border: "1.5px solid #C2D0B9",
            backgroundColor: "var(--lp-bg-card)",
            fontSize: "0.83rem",
            color: "var(--lp-text-dark)",
            cursor: "pointer",
            outline: "none",
          }}
        >
          <option value="all">All Types</option>
          <option value="mandatory">Required</option>
          <option value="elective">Elective</option>
        </select>

        {/* Semester filter */}
        <select
          value={semesterFilter}
          onChange={(e) =>
            setSemesterFilter(e.target.value as "all" | "fall" | "spring" | "summer")
          }
          style={{
            fontFamily: "'Nunito', sans-serif",
            padding: "0.45rem 0.9rem",
            borderRadius: "0.75rem",
            border: "1.5px solid #C2D0B9",
            backgroundColor: "var(--lp-bg-card)",
            fontSize: "0.83rem",
            color: "var(--lp-text-dark)",
            cursor: "pointer",
            outline: "none",
          }}
        >
          <option value="all">All Semesters</option>
          <option value="fall">Fall</option>
          <option value="spring">Spring</option>
          <option value="summer">Summer</option>
        </select>

        {/* Live count */}
        <span style={{
          fontFamily: "'Nunito', sans-serif",
          fontSize: "0.78rem", fontWeight: 600,
          color: "var(--lp-text-heading)", whiteSpace: "nowrap",
        }}>
          {filtered.length} of {courses.length} shown
        </span>
      </div>

      {/* Course grid */}
      {filtered.length === 0 ? (
        <div style={{
          textAlign: "center",
          padding: "3rem",
          fontFamily: "'Nunito', sans-serif",
          color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.92rem",
          backgroundColor: "var(--lp-bg-secondary)",
          borderRadius: "1rem",
        }}>
          No courses match your filters.
        </div>
      ) : (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(270px, 1fr))",
          gap: "0.875rem",
        }}>
          {filtered.map((c) => (
            <EligibleCourseCard key={c.Code} course={c} />
          ))}
        </div>
      )}
    </>
  );
}

// â”€â”€ Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export function RemainingCoursesPage() {
  const { appData } = useAppData();
  const navigate    = useNavigate();

  useEffect(() => {
    if (!appData) navigate("/", { replace: true });
  }, [appData, navigate]);

  if (!appData) return null;

  const courses = appData.allEligibleCourses;

  // Build chatbot context so the AI knows what the user is looking at
  const remainingContext = (() => {
    const required = courses.filter(c => !c.Is_elective).length;
    const elective = courses.filter(c => c.Is_elective).length;
    const failed   = courses.filter(c => c.is_failed).length;
    const preview  = courses.slice(0, 20)
      .map(c =>
        `  - ${c.Code} | ${c.Course_Name} (${c.Credit_Hours} cr, Level ${c.Level ?? "?"}, ` +
        `${c.Is_elective ? "Elective" : "Required"}${c.is_failed ? ", FAILED — needs retake" : ""})`
      )
      .join("\n");
    return [
      "User is viewing the All Remaining Courses page — every course not yet passed.",
      `Total: ${courses.length} courses (${required} required, ${elective} elective` +
        (failed > 0 ? `, ${failed} need retaking` : "") + ").",
      `First ${Math.min(20, courses.length)} listed:\n${preview}`,
      courses.length > 20 ? `...and ${courses.length - 20} more.` : "",
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
        <Sidebar activePage="remaining" />

        <main
          style={{
            flex: 1,
            minWidth: 0,
            padding: "1.75rem 2rem 3rem",
            backgroundColor: "var(--lp-bg-card)",
          }}
        >
          {/* Page intro */}
          <div style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "0.75rem",
            marginBottom: "0.5rem",
          }}>
            <div>
              <p style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-accent)", fontWeight: 700,
                fontSize: "0.78rem", letterSpacing: "0.1em",
                textTransform: "uppercase", marginBottom: "0.25rem",
              }}>
                Browse your curriculum
              </p>
              <h1 style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-dark)", fontWeight: 800, fontSize: "1.75rem",
              }}>
                All Remaining Courses
              </h1>
              <p style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-heading)", fontWeight: 500, fontSize: "0.95rem",
                marginTop: "0.35rem",
              }}>
                Every course you have to register for your academic trip, except the ones you've already taken.
              </p>
            </div>
            <span style={{
              fontFamily: "'Nunito', sans-serif",
              fontWeight: 800, fontSize: "0.8rem",
              color: "#fff", backgroundColor: "#A8BE83",
              padding: "5px 14px", borderRadius: "9999px",
              whiteSpace: "nowrap", alignSelf: "flex-start",
            }}>
              {courses.length} courses
            </span>
          </div>

          {/* Divider */}
          <div style={{
            height: "1px",
            backgroundColor: "var(--lp-bg-secondary)",
            borderRadius: "9999px",
            margin: "1.25rem 0 1.75rem",
          }} />

          <CourseList courses={courses} />
        </main>
      </div>

      <Footer />
      <ChatbotFAB pageContext={remainingContext} />
    </div>
  );
}



