import { BookOpen, Clock, Star, AlertTriangle, CheckCircle } from "lucide-react";
import {
  TOP_COURSES,
  ALT_COURSES,
  getBadgeConfig,
  computeScore,
  type CourseData,
  type GradeProbabilities,
} from "../../data/courses";

// â”€â”€ ML bucket constants (mirrors ml/data_loader.py) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const BUCKET_ORDER = ["Excellent", "Good", "Average", "Low", "Fail"] as const;
type GradeBucket = (typeof BUCKET_ORDER)[number];

const BUCKET_TO_GRADES: Record<GradeBucket, string> = {
  Excellent: "A, A-",
  Good:      "B+, B",
  Average:   "C+, C",
  Low:       "D",
  Fail:      "F",
};

// Segment colours for the probability bar
const BUCKET_BAR_COLOR: Record<GradeBucket, string> = {
  Excellent: "#9CA35A",
  Good:      "#A8BE83",
  Average:   "#F2C27F",
  Low:       "#E8A87C",
  Fail:      "#C87330",
};

// Chip colours for the predicted-grade badge and probability pills
const BUCKET_CHIP: Record<GradeBucket, { color: string; bg: string }> = {
  Excellent: { color: "var(--lp-text-dark)", bg: "#E8F0DC" },
  Good:      { color: "var(--lp-text-dark)", bg: "#C2D0B9" },
  Average:   { color: "#7A5C00", bg: "#FDF0D0" },
  Low:       { color: "#7D3C00", bg: "#FFE0C0" },
  Fail:      { color: "#fff",    bg: "#C87330" },
};

// Derive the highest-probability bucket from grade_probabilities
function getPredictedBucket(probs: GradeProbabilities): GradeBucket {
  return BUCKET_ORDER.reduce<GradeBucket>((best, b) =>
    (probs[b] ?? 0) > (probs[best] ?? 0) ? b : best,
    "Excellent"
  );
}

// â”€â”€ Icon selector â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function getCourseIcon(score: number) {
  if (score < 50) return AlertTriangle;
  if (score >= 60) return Star;
  return CheckCircle;

}

// â”€â”€ Probability distribution bar + pill row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function MLProbabilityDisplay({ probs }: { probs: GradeProbabilities }) {
  return (
    <div style={{ marginTop: "0.55rem" }}>
      {/* Segmented bar â€” 5 colour segments proportional to probability */}
      <div style={{
        display: "flex",
        height: "6px",
        borderRadius: "9999px",
        overflow: "hidden",
        gap: "2px",
        backgroundColor: "var(--lp-bg-secondary)",
      }}>
        {BUCKET_ORDER.map((bucket) => {
          const pct = (probs[bucket] ?? 0) * 100;
          if (pct < 0.5) return null;
          return (
            <div
              key={bucket}
              title={`${bucket}: ${Math.round(pct)}%`}
              style={{
                width: `${pct}%`,
                backgroundColor: BUCKET_BAR_COLOR[bucket],
                transition: "width 0.6s ease",
                flexShrink: 0,
              }}
            />
          );
        })}
      </div>

      {/* Probability pills â€” only for buckets with â‰¥ 1 % */}
      <div style={{
        display: "flex",
        gap: "4px",
        flexWrap: "wrap",
        marginTop: "0.3rem",
      }}>
        {BUCKET_ORDER.map((bucket) => {
          const pct = Math.round((probs[bucket] ?? 0) * 100);
          if (pct < 1) return null;
          const chip = BUCKET_CHIP[bucket];
          return (
            <span
              key={bucket}
              style={{
                fontFamily: "'Nunito', sans-serif",
                fontSize: "0.6rem",
                fontWeight: 700,
                color: chip.color,
                backgroundColor: chip.bg,
                padding: "1px 6px",
                borderRadius: "9999px",
              }}
            >
              {bucket[0]}: {pct}%
            </span>
          );
        })}
      </div>
    </div>
  );
}

// â”€â”€ Score bar (Option B: Excellent + Good probability) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function ScoreBar({ score, color }: { score: number; color: string }) {
  // Round the score to avoid long decimal numbers (e.g., 85.4% -> 85%)
  const displayScore = Math.round(score);

  return (
    <div style={{ width: "100%", marginTop: "0.4rem" }}>
      
      {/* Score Label Container: Centered above the bar */}
      <div style={{
        display: "flex", 
        justifyContent: "center", // Centers the text horizontally
        alignItems: "center",     // Aligns items vertically
        fontSize: "0.75rem",      // Small, clean font size
        fontWeight: "600",        // Bold text for readability
        color: color,             // Matches the bar's color for consistency
        marginBottom: "0.3rem",   // Space between the text and the bar
        letterSpacing: "0.5px"    // Slight letter spacing for a modern UI look
      }}>
        High Grade Probability: {displayScore}%
      </div>

      {/* The actual progress bar track */}
      <div style={{
        width: "100%", height: "5px",
        backgroundColor: "var(--lp-bg-secondary)",
        borderRadius: "9999px",
        overflow: "hidden",
      }}>
        {/* The filled part of the progress bar */}
        <div style={{
          width: `${displayScore}%`, // Uses the rounded score for the fill width
          height: "100%",
          backgroundColor: color,
          borderRadius: "9999px",
          transition: "width 0.6s ease",
        }} />
      </div>
    </div>
  );
}
// â”€â”€ Individual Course Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function CourseCard({ course }: { course: CourseData }) {
  const score          = computeScore(course.grade_probabilities);
  const badge          = getBadgeConfig(score);
  const Icon           = getCourseIcon(score);
  const predictedBucket = getPredictedBucket(course.grade_probabilities);
  const chip           = BUCKET_CHIP[predictedBucket];

  return (
    <div
      style={{
        backgroundColor: "var(--lp-bg-card)",
        borderRadius: "1.25rem",
        borderLeft: `4px solid ${badge.borderColor}`,
        padding: "1rem 1.25rem",
        display: "flex",
        alignItems: "flex-start",
        gap: "0.875rem",
        boxShadow: "0 3px 14px rgba(79,83,33,0.07)",
        transition: "transform 0.18s, box-shadow 0.18s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateX(4px)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 6px 22px rgba(79,83,33,0.12)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateX(0)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 3px 14px rgba(79,83,33,0.07)";
      }}
    >
      {/* Icon box */}
      <div style={{
        width: "40px", height: "40px", minWidth: "40px",
        borderRadius: "0.75rem",
        backgroundColor: `${badge.borderColor}22`,
        display: "flex", alignItems: "center", justifyContent: "center",
        marginTop: "2px",
      }}>
        <Icon size={18} color={badge.iconColor} strokeWidth={2} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>

        {/* Name + code */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <span style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-dark)", fontWeight: 800, fontSize: "0.98rem",
          }}>
            {course.name}
          </span>
          <span style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.75rem",
            backgroundColor: "var(--lp-bg-secondary)",
            padding: "1px 8px", borderRadius: "9999px",
          }}>
            {course.code}
          </span>
        </div>

        {/* Badge + credit hours */}
        <div style={{
          display: "flex", alignItems: "center", gap: "0.6rem",
          marginTop: "0.35rem", flexWrap: "wrap",
        }}>
          <span style={{
            fontFamily: "'Nunito', sans-serif",
            color: badge.badgeColor, fontWeight: 700, fontSize: "0.72rem",
            backgroundColor: badge.badgeBg,
            padding: "2px 10px", borderRadius: "9999px",
          }}>
            {badge.badge}
          </span>
          <span style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.75rem",
            display: "flex", alignItems: "center", gap: "3px",
          }}>
            <Clock size={11} /> {course.creditHours} cr hrs
          </span>
        </div>

        <ScoreBar score={score} color={badge.borderColor} />

        {/* â”€â”€ ML Output â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        <div style={{
          marginTop: "0.65rem",
          paddingTop: "0.6rem",
          borderTop: "1px dashed #C2D0B9",
        }}>
          {/* Predicted grade chip + grade range */}
          <div style={{
            display: "flex", alignItems: "center", gap: "0.4rem",
            flexWrap: "wrap", marginBottom: "0.35rem",
          }}>
            <span style={{
              fontFamily: "'Nunito', sans-serif",
              fontSize: "0.68rem", fontWeight: 600, color: "var(--lp-text-heading)",
            }}>
              ML Prediction:
            </span>
            <span style={{
              fontFamily: "'Nunito', sans-serif",
              fontSize: "0.7rem", fontWeight: 800,
              color: chip.color,
              backgroundColor: chip.bg,
              padding: "2px 9px", borderRadius: "9999px",
            }}>
              {predictedBucket}
            </span>
            <span style={{
              fontFamily: "'Nunito', sans-serif",
              fontSize: "0.68rem", fontWeight: 600,
              color: "var(--lp-text-heading)",
              backgroundColor: "var(--lp-bg-secondary)",
              padding: "2px 8px", borderRadius: "9999px",
            }}>
              {BUCKET_TO_GRADES[predictedBucket]}
            </span>
          </div>

          {/* Probability bar + pills */}
          <MLProbabilityDisplay probs={course.grade_probabilities} />
        </div>

        {/* Note */}
        {course.note && (
          <p style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-heading)", fontWeight: 500, fontSize: "0.78rem",
            marginTop: "0.5rem", lineHeight: 1.5,
          }}>
            {course.note}
          </p>
        )}
      </div>
    </div>
  );
}

// â”€â”€ Column header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function ColumnHeader({ dotColor, title }: { dotColor: string; title: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.875rem" }}>
      <div style={{
        width: "10px", height: "10px",
        backgroundColor: dotColor, borderRadius: "50%",
      }} />
      <h3 style={{
        fontFamily: "'Nunito', sans-serif",
        color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.92rem", letterSpacing: "0.03em",
      }}>
        {title}
      </h3>
    </div>
  );
}

// â”€â”€ Main Export â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// topCourses / altCourses are optional: when the real API is wired up,
// pass the backend's pre-sorted arrays directly; placeholder data is used otherwise.
export function RecommendedCourses({
  topCourses = TOP_COURSES,
  altCourses  = ALT_COURSES,
}: {
  topCourses?: CourseData[];
  altCourses?:  CourseData[];
} = {}) {
  return (
    <section id="recommendations">
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
        gap: "1.5rem",
      }}>
        {/* Column A â€” Top Recommended */}
        <div>
          <ColumnHeader dotColor="#A8BE83" title="Top Recommended Courses" />
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {topCourses.map((c) => (
              <CourseCard key={c.id} course={c} />
            ))}
          </div>
        </div>

        {/* Column B â€” Alternative Courses */}
        <div>
          <ColumnHeader dotColor="#F2C27F" title="Alternative Courses" />
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {altCourses.map((c) => (
              <CourseCard key={c.id} course={c} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

