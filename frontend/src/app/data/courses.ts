// ── Shared course data used by Dashboard, Recommendations & GPA Simulator ─────

export type GradeProbabilities = {
  Excellent: number;
  Good: number;
  Average: number;
  Low: number;
  Fail: number;
};

export type CourseData = {
  id: string;
  name: string;
  code: string;
  creditHours: number;
  mandatory: boolean;
  note?: string;
  grade_probabilities: GradeProbabilities;
};

export type BadgeConfig = {
  badge: string;
  badgeColor: string;
  badgeBg: string;
  borderColor: string;
  iconColor: string;
};

// Option B: sum of Excellent + Good probabilities × 100
export function computeScore(probs: GradeProbabilities): number {
  return Math.round((probs.Excellent + probs.Good) * 100);
}

export function getBadgeConfig(score: number): BadgeConfig {
  if ( score < 50) {
    return {
      badge: "Requires Effort",
      badgeColor: "#fff",
      badgeBg: "#C87330",
      borderColor: "#C87330",
      iconColor: "#C87330",
    };
  }
  if (score >= 60) {
    return {
      badge: "Perfect Match",
      badgeColor: "#4F5321",
      badgeBg: "#C2D0B9",
      borderColor: "#A8BE83",
      iconColor: "#A8BE83",
    };
  }
  return {
    badge: "Good Fit",
    badgeColor: "#4F5321",
    badgeBg: "#DEDBD2",
    borderColor: "#C2D0B9",
    iconColor: "#9CA35A",
  };
}
export const ALL_COURSES: CourseData[] = [
  {
    id: "ds",
    name: "Data Structures",
    code: "CS 201",
    creditHours: 3,
    mandatory: false,
    grade_probabilities: { Excellent: 0.65, Good: 0.27, Average: 0.06, Low: 0.02, Fail: 0.00 },
  },
  {
    id: "se",
    name: "Software Engineering",
    code: "CS 301",
    creditHours: 3,
    mandatory: false,
    grade_probabilities: { Excellent: 0.50, Good: 0.35, Average: 0.12, Low: 0.03, Fail: 0.00 },
  },
  {
    id: "ld",
    name: "Logic Design",
    code: "CS 211",
    creditHours: 3,
    mandatory: false,
    grade_probabilities: { Excellent: 0.35, Good: 0.43, Average: 0.17, Low: 0.05, Fail: 0.00 },
  },
  {
    id: "db",
    name: "Database Systems",
    code: "CS 322",
    creditHours: 3,
    mandatory: false,
    grade_probabilities: { Excellent: 0.28, Good: 0.44, Average: 0.20, Low: 0.08, Fail: 0.00 },
  },
  {
    id: "discrete",
    name: "Discrete Mathematics",
    code: "MATH 301",
    creditHours: 3,
    mandatory: true,
    note: "Mandatory prerequisite — challenging history.",
    grade_probabilities: { Excellent: 0.15, Good: 0.40, Average: 0.28, Low: 0.12, Fail: 0.05 },
  },
];

// ── Partition: Top Recommended vs Alternative ─────────────────────────────────
// Non-mandatory courses sorted by score desc fill Top up to CREDIT_LIMIT.
// Overflow + all mandatory courses go to Alternative.
const CREDIT_LIMIT = 9;

const _nonMandatory = [...ALL_COURSES]
  .filter((c) => !c.mandatory)
  .sort((a, b) => computeScore(b.grade_probabilities) - computeScore(a.grade_probabilities));

const _mandatory = ALL_COURSES.filter((c) => c.mandatory);

let _acc = 0;
export const TOP_COURSES: CourseData[] = [];
export const ALT_COURSES: CourseData[] = [];

for (const c of _nonMandatory) {
  if (_acc + c.creditHours <= CREDIT_LIMIT) {
    TOP_COURSES.push(c);
    _acc += c.creditHours;
  } else {
    ALT_COURSES.push(c);
  }
}
ALT_COURSES.push(..._mandatory);

export const BASE_CURRENT_GPA = 3.24;
