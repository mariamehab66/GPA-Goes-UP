import { useState, useMemo, useEffect, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  TooltipProps,
} from "recharts";
import {
  getBadgeConfig,
  computeScore,
  type CourseData,
} from "../../data/courses";
import { useAppData, toCourseData } from "../../context/AppDataContext";

// ── Toggle Switch ─────────────────────────────────────────────────────────────
function Toggle({ on, onChange }: { on: boolean; onChange: () => void }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={(e) => { e.stopPropagation(); onChange(); }}
      style={{
        width: "44px",
        height: "24px",
        borderRadius: "9999px",
        border: "none",
        cursor: "pointer",
        backgroundColor: on ? "#A8BE83" : "#C2D0B9",
        position: "relative",
        transition: "background-color 0.25s ease",
        flexShrink: 0,
        outline: "none",
      }}
    >
      <span
        style={{
          position: "absolute",
          top: "3px",
          left: on ? "23px" : "3px",
          width: "18px",
          height: "18px",
          borderRadius: "50%",
          backgroundColor: "#fff",
          boxShadow: "0 1px 4px rgba(0,0,0,0.2)",
          transition: "left 0.25s ease",
        }}
      />
    </button>
  );
}

// ── Custom Tooltip ────────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const filtered = payload.filter(
    (entry) => !(entry.name === "Predicted GPA" && label !== "Next Sem"),
  );
  return (
    <div
      style={{
        backgroundColor: "var(--lp-bg-card)",
        border: "1.5px solid #C2D0B9",
        borderRadius: "0.875rem",
        padding: "0.75rem 1rem",
        boxShadow: "0 6px 20px rgba(79,83,33,0.12)",
        fontFamily: "'Nunito', sans-serif",
      }}
    >
      <p style={{ color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.85rem", marginBottom: "0.3rem" }}>
        {label}
      </p>
      {filtered.map((entry) => (
        <p key={entry.name} style={{ color: entry.color as string, fontWeight: 600, fontSize: "0.82rem" }}>
          {entry.name}: {typeof entry.value === "number" ? entry.value.toFixed(3) : "—"}
        </p>
      ))}
    </div>
  );
}

// ── Course toggle row ─────────────────────────────────────────────────────────
function CourseToggleRow({
  course,
  isOn,
  onToggle,
}: {
  course: CourseData;
  isOn: boolean;
  onToggle: () => void;
}) {
  const badge = getBadgeConfig(computeScore(course.grade_probabilities));

  return (
    <div
      onClick={onToggle}
      style={{
        backgroundColor: isOn ? `${badge.borderColor}15` : "var(--lp-bg-card)",
        borderRadius: "1rem",
        padding: "0.75rem 1rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "0.75rem",
        cursor: "pointer",
        border: `1.5px solid ${isOn ? badge.borderColor : "transparent"}`,
        transition: "background-color 0.2s, border-color 0.2s",
        boxShadow: isOn ? `0 2px 10px ${badge.borderColor}28` : "none",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flex: 1, minWidth: 0 }}>
        <div
          style={{
            width: "10px",
            height: "10px",
            minWidth: "10px",
            borderRadius: "50%",
            backgroundColor: badge.borderColor,
            opacity: isOn ? 1 : 0.35,
            transition: "opacity 0.2s",
          }}
        />
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
            <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.92rem" }}>
              {course.name}
            </span>
            <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.72rem", backgroundColor: "var(--lp-bg-secondary)", padding: "1px 7px", borderRadius: "9999px" }}>
              {course.code}
            </span>
            <span style={{ fontFamily: "'Nunito', sans-serif", color: badge.badgeColor, fontWeight: 700, fontSize: "0.68rem", backgroundColor: badge.badgeBg, padding: "1px 7px", borderRadius: "9999px", border: `1px solid ${badge.borderColor}55` }}>
              {badge.badge}
            </span>
          </div>
          <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.75rem", marginTop: "2px", display: "block" }}>
            Score: {computeScore(course.grade_probabilities)}% · {course.creditHours} cr hrs
          </span>
        </div>
      </div>
      <Toggle on={isOn} onChange={onToggle} />
    </div>
  );
}

// ── Group header ──────────────────────────────────────────────────────────────
function GroupLabel({ dotColor, title }: { dotColor: string; title: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
      <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: dotColor }} />
      <span style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.78rem", letterSpacing: "0.04em", textTransform: "uppercase" }}>
        {title}
      </span>
    </div>
  );
}

// ── EV range helpers ──────────────────────────────────────────────────────────
type GradeBucket = "Excellent" | "Good" | "Average" | "Low" | "Fail";

const BUCKET_MIN: Record<GradeBucket, number> = { Excellent: 3.67, Good: 3.00, Average: 2.33, Low: 2.00, Fail: 0.00 };
const BUCKET_MAX: Record<GradeBucket, number> = { Excellent: 4.00, Good: 3.33, Average: 2.67, Low: 2.00, Fail: 0.00 };

function dominantBucket(p: CourseData["grade_probabilities"]): GradeBucket {
  return (Object.entries(p) as [GradeBucket, number][]).reduce((a, b) => (b[1] > a[1] ? b : a))[0];
}
function courseMinEV(p: CourseData["grade_probabilities"]): number { return BUCKET_MIN[dominantBucket(p)]; }
function courseMaxEV(p: CourseData["grade_probabilities"]): number { return BUCKET_MAX[dominantBucket(p)]; }
const signed3 = (n: number) => (n >= 0 ? `+${n.toFixed(3)}` : n.toFixed(3));

// ── Main Export ───────────────────────────────────────────────────────────────
export function GPASimulator({ onContextChange }: { onContextChange?: (ctx: string) => void } = {}) {
  const { appData } = useAppData();
  const stats       = appData!.stats;
  const topCourses  = appData!.topRecommended.map(c => toCourseData(c));
  const altCourses  = appData!.alternativeCourses.map(c => toCourseData(c));
  const allCourses  = [...topCourses, ...altCourses];

  const [selected, setSelected] = useState<Record<string, boolean>>(
    Object.fromEntries(allCourses.map((c) => [c.id, false]))
  );
  const [limitMsg, setLimitMsg] = useState(false);
  const limitTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => { if (limitTimer.current) clearTimeout(limitTimer.current); }, []);

  const dynamicHours  = allCourses.filter(c => selected[c.id]).reduce((s, c) => s + c.creditHours, 0);
  const selectedCount = Object.values(selected).filter(Boolean).length;

  // Report current simulator state to chatbot whenever selection changes
  useEffect(() => {
    if (!onContextChange) return;
    const courses = allCourses.filter(c => selected[c.id]);
    const hours   = courses.reduce((s, c) => s + c.creditHours, 0);
    if (hours === 0) {
      onContextChange("User is on the GPA Simulator. No courses have been toggled on yet.");
      return;
    }
    const minW   = courses.reduce((s, c) => s + courseMinEV(c.grade_probabilities) * c.creditHours, 0);
    const maxW   = courses.reduce((s, c) => s + courseMaxEV(c.grade_probabilities) * c.creditHours, 0);
    const semMin = Math.min(4.0, minW / hours);
    const semMax = Math.min(4.0, maxW / hours);
    const lines  = courses
      .map(c => `  - ${c.code} | ${c.name} (${c.creditHours} cr) — predicted: ${dominantBucket(c.grade_probabilities)}`)
      .join("\n");
    onContextChange(
      `User is on the GPA Simulator.\n` +
      `${courses.length} course(s) selected, ${hours} / ${appData!.maxAllowedHours} allowed credit hours.\n` +
      `Selected courses:\n${lines}\n` +
      `Predicted next semester GPA range: ${semMin.toFixed(3)} – ${semMax.toFixed(3)}\n` +
      `Change vs last semester GPA (${stats.lastSemGpa.toFixed(3)}): ${signed3(semMin - stats.lastSemGpa)} to ${signed3(semMax - stats.lastSemGpa)}`
    );
  }, [selected]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id: string) => {
    const course = allCourses.find(c => c.id === id)!;
    if (!selected[id] && dynamicHours + course.creditHours > appData!.maxAllowedHours) {
      setLimitMsg(true);
      if (limitTimer.current) clearTimeout(limitTimer.current);
      limitTimer.current = setTimeout(() => setLimitMsg(false), 3000);
      return;
    }
    setSelected(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Range-based GPA simulation
  const sim = useMemo(() => {
    const courses = allCourses.filter(c => selected[c.id]);
    const hours   = courses.reduce((s, c) => s + c.creditHours, 0);
    if (hours === 0) return { semMin: 0, semMax: 0 };
    const minWeighted = courses.reduce((s, c) => s + courseMinEV(c.grade_probabilities) * c.creditHours, 0);
    const maxWeighted = courses.reduce((s, c) => s + courseMaxEV(c.grade_probabilities) * c.creditHours, 0);
    return {
      semMin: Math.min(4.0, minWeighted / hours),
      semMax: Math.min(4.0, maxWeighted / hours),
    };
  }, [selected]);

  // Sort history: ascending by year, then Fall → Spring → Summer within same year
  const parseSemKey = (sem: string): [number, number] => {
    const m = sem.match(/^(\w+)\s+'(\d{2})/);
    if (!m) return [0, 0];
    const seasonOrder: Record<string, number> = { Fall: 1, Spring: 2, Summer: 3 };
    return [parseInt(m[2], 10), seasonOrder[m[1]] ?? 99];
  };
  const sortedHistory = [...stats.semesterHistory].sort((a, b) => {
    const [yearA, seaA] = parseSemKey(a.sem);
    const [yearB, seaB] = parseSemKey(b.sem);
    return yearA !== yearB ? yearA - yearB : seaA - seaB;
  });

  // Chart uses midpoint for the predicted line
  const chartPredicted = dynamicHours === 0 ? stats.cgpa : (sim.semMin + sim.semMax) / 2;
  const chartData = [
    ...sortedHistory.map(e => ({ semester: e.sem, gpa: e.gpa, predicted: null as number | null })),
    { semester: "Next Sem", gpa: null as number | null, predicted: chartPredicted },
  ].map((d, i, arr) => (i === arr.length - 2 ? { ...d, predicted: d.gpa } : d));

  // Diffs for card arrow
  const semDiffMin = parseFloat((sim.semMin - stats.lastSemGpa).toFixed(3));
  const semDiffMax = parseFloat((sim.semMax - stats.lastSemGpa).toFixed(3));

  // Card border color based on midpoint
  const semMid   = (sim.semMin + sim.semMax) / 2;
  const semColor = dynamicHours === 0 ? "#C2D0B9" : semMid >= 3.0 ? "#A8BE83" : semMid >= 2.5 ? "#F2C27F" : "#C87330";

  return (
    <section id="simulator" style={{ marginTop: "2rem" }}>
      <div style={{ backgroundColor: "var(--lp-bg-secondary)", borderRadius: "1.75rem", padding: "1.75rem", boxShadow: "0 6px 28px rgba(79,83,33,0.10)" }}>

        {/* ── Header ──────────────────────────────────────────────────────── */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
          <div>
            <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-accent)", fontWeight: 700, fontSize: "0.78rem", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "0.2rem" }}>
              Interactive · Real-Time
            </p>
            <h2 style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 800, fontSize: "1.5rem" }}>
              GPA Simulator 
            </h2>
          </div>

          {/* ── Predicted Semester GPA card ───────────────────────────────── */}
          <div style={{ backgroundColor: "var(--lp-bg-card)", borderRadius: "1.25rem", padding: "0.85rem 2rem", textAlign: "center", boxShadow: "0 3px 12px rgba(79,83,33,0.08)", minWidth: "200px", borderTop: `3px solid ${semColor}` }}>
            <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.72rem" }}>
              Predicted Semester GPA
            </p>
            {dynamicHours === 0 ? (
              <>
                <p style={{ fontFamily: "'Nunito', sans-serif", color: "#C2D0B9", fontWeight: 900, fontSize: "2rem", lineHeight: 1.1 }}>---</p>
                <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 600, fontSize: "0.75rem", marginTop: "0.15rem" }}>Select courses below</p>
              </>
            ) : (
              <>
                <p style={{ fontFamily: "'Nunito', sans-serif", color: semColor, fontWeight: 900, fontSize: "1.65rem", lineHeight: 1.1 }}>
                  {sim.semMin.toFixed(3)} – {sim.semMax.toFixed(3)}
                </p>
                <p style={{ fontFamily: "'Nunito', sans-serif", color: semDiffMin >= 0 ? "#9CA35A" : "#C87330", fontWeight: 700, fontSize: "0.75rem", marginTop: "0.15rem" }}>
                  {semDiffMin >= 0 ? "↑" : "↓"} {signed3(semDiffMin)} ~ {signed3(semDiffMax)} pts
                </p>
              </>
            )}
          </div>
        </div>

        {/* ── Chart ───────────────────────────────────────────────────────── */}
        <div style={{ backgroundColor: "var(--lp-bg-card)", borderRadius: "1.25rem", padding: "1.25rem 0.5rem 0.5rem", marginBottom: "1.5rem" }}>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData} margin={{ top: 8, right: 24, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="4 4" stroke="#C2D0B9" vertical={false} />
              <XAxis
                dataKey="semester"
                tick={{ fontFamily: "'Nunito', sans-serif", fill: "#88734B", fontSize: 12, fontWeight: 600 }}
                axisLine={{ stroke: "#C2D0B9" }}
                tickLine={false}
              />
              <YAxis
                domain={[2.4, 4.0]}
                tickCount={5}
                tickFormatter={(v) => v.toFixed(1)}
                tick={{ fontFamily: "'Nunito', sans-serif", fill: "#88734B", fontSize: 11, fontWeight: 600 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontFamily: "'Nunito', sans-serif", fontSize: "0.8rem", paddingTop: "8px" }}
                formatter={(value) => <span style={{ color: "var(--lp-text-heading)", fontWeight: 600 }}>{value}</span>}
              />
              <ReferenceLine
                y={3.0}
                stroke="#9CA35A"
                strokeDasharray="6 3"
                strokeWidth={1.5}
                label={{ value: "3.0 Target", fill: "#9CA35A", fontSize: 10, fontFamily: "'Nunito', sans-serif" }}
              />
              <Line
                type="monotone"
                dataKey="gpa"
                name="Historical GPA"
                stroke="#88734B"
                strokeWidth={2.5}
                dot={{ fill: "#88734B", r: 4, strokeWidth: 0 }}
                activeDot={{ r: 6, fill: "#88734B" }}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="predicted"
                name="Predicted GPA"
                stroke="#A8BE83"
                strokeWidth={2.5}
                strokeDasharray="7 4"
                dot={(props: any) => {
                  if (props.payload.gpa != null)
                    return <circle key={props.index} cx={props.cx} cy={props.cy} r={0} fill="none" />;
                  return <circle key={props.index} cx={props.cx} cy={props.cy} r={4} fill="#A8BE83" />;
                }}
                activeDot={(props: any) => {
                  if (props.payload.gpa != null)
                    return <circle key={`a${props.index}`} cx={props.cx} cy={props.cy} r={0} fill="none" />;
                  return <circle key={`a${props.index}`} cx={props.cx} cy={props.cy} r={6} fill="#A8BE83" />;
                }}
                connectNulls={true}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* ── Credit limit message ─────────────────────────────────────────── */}
        {limitMsg && (
          <div style={{ backgroundColor: "#FFF3E0", border: "1.5px solid #C87330", borderRadius: "0.875rem", padding: "0.6rem 1rem", marginBottom: "1rem", fontFamily: "'Nunito', sans-serif", color: "#C87330", fontWeight: 700, fontSize: "0.85rem" }}>
            ⚠ Cannot add course — exceeds your {appData!.maxAllowedHours} credit hour limit.
          </div>
        )}

        {/* ── Summary pills ────────────────────────────────────────────────── */}
        <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap", marginBottom: "1.25rem" }}>
          <div style={{ fontFamily: "'Nunito', sans-serif", fontSize: "0.8rem", fontWeight: 700, color: "var(--lp-text-dark)", backgroundColor: "var(--lp-bg-primary)", padding: "4px 12px", borderRadius: "9999px" }}>
            {selectedCount} course{selectedCount !== 1 ? "s" : ""} selected
          </div>
          <div style={{ fontFamily: "'Nunito', sans-serif", fontSize: "0.8rem", fontWeight: 700, color: "var(--lp-text-dark)", backgroundColor: "var(--lp-bg-primary)", padding: "4px 12px", borderRadius: "9999px" }}>
            {dynamicHours} / {appData!.maxAllowedHours} credit hours
          </div>
          {dynamicHours > 0 && semDiffMin > 0 && (
            <div style={{ fontFamily: "'Nunito', sans-serif", fontSize: "0.8rem", fontWeight: 700, color: "#fff", backgroundcolor: "var(--lp-text-accent)", padding: "4px 12px", borderRadius: "9999px" }}>
              📈 GPA improving!
            </div>
          )}
          {dynamicHours > 0 && semDiffMax < 0 && (
            <div style={{ fontFamily: "'Nunito', sans-serif", fontSize: "0.8rem", fontWeight: 700, color: "#fff", backgroundColor: "#C87330", padding: "4px 12px", borderRadius: "9999px" }}>
              ⚠️ GPA at risk
            </div>
          )}
          {dynamicHours > 0 && semDiffMin <= 0 && semDiffMax >= 0 && (
            <div style={{ fontFamily: "'Nunito', sans-serif", fontSize: "0.8rem", fontWeight: 700, color: "var(--lp-text-dark)", backgroundColor: "var(--lp-bg-secondary)", padding: "4px 12px", borderRadius: "9999px" }}>
              ↔ GPA stable
            </div>
          )}
        </div>

        {/* ── Toggle list ──────────────────────────────────────────────────── */}
        <div>
          <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 700, fontSize: "0.85rem", marginBottom: "0.875rem", letterSpacing: "0.04em" }}>
            Toggle courses to simulate your semester plan:
          </p>
          <div style={{ marginBottom: "1rem" }}>
            <GroupLabel dotColor="#A8BE83" title="Top Recommended" />
            <div style={{ display: "flex", flexDirection: "column", gap: "0.55rem" }}>
              {topCourses.map((course) => (
                <CourseToggleRow key={course.id} course={course} isOn={selected[course.id]} onToggle={() => toggle(course.id)} />
              ))}
            </div>
          </div>
          <div>
            <GroupLabel dotColor="#F2C27F" title="Alternative Courses" />
            <div style={{ display: "flex", flexDirection: "column", gap: "0.55rem" }}>
              {altCourses.map((course) => (
                <CourseToggleRow key={course.id} course={course} isOn={selected[course.id]} onToggle={() => toggle(course.id)} />
              ))}
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}


