import { Upload, CalendarCog, TrendingUp } from "lucide-react";

const steps = [
  {
    icon: Upload,
    title: "1. Upload Transcript",
    text: "Securely drop your Arabic PDF record.",
    accent: "#A8BE83",
    emoji: "📄",
  },
  {
    icon: CalendarCog,
    title: "2. Select Semester",
    text: "Choose which semester you want to optimize.",
    accent: "#F2C27F",
    emoji: "📅",
  },
  {
    icon: TrendingUp,
    title: "3. See the Magic Happen",
    text: "View smart course combinations to boost your GPA.",
    accent: "#9CA35A",
    emoji: "✨",
  },
];

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      style={{ backgroundColor: "var(--lp-bg-primary)" }}
      className="w-full py-20 px-6"
    >
      <div className="max-w-5xl mx-auto">
        {/* Title */}
        <div className="text-center mb-14">
          <p
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-accent)",
              fontWeight: 700,
              fontSize: "0.85rem",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              marginBottom: "0.5rem",
            }}
          >
            Simple Process
          </p>
          <h2
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-heading)",
              fontWeight: 800,
              fontSize: "2rem",
            }}
          >
            Your Path to a Higher GPA
          </h2>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-7">
          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <div
                key={step.title}
                style={{
                  backgroundColor: "var(--lp-bg-secondary)",
                  borderRadius: "1.75rem",
                  padding: "2.25rem 2rem",
                  boxShadow: "0 6px 28px rgba(79,83,33,0.10)",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  textAlign: "center",
                  gap: "1rem",
                  position: "relative",
                  overflow: "hidden",
                  transition: "transform 0.2s, box-shadow 0.2s",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLDivElement).style.transform = "translateY(-5px)";
                  (e.currentTarget as HTMLDivElement).style.boxShadow =
                    "0 14px 40px rgba(79,83,33,0.16)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
                  (e.currentTarget as HTMLDivElement).style.boxShadow =
                    "0 6px 28px rgba(79,83,33,0.10)";
                }}
              >
                {/* Step number badge */}
                <div
                  style={{
                    position: "absolute",
                    top: "1.1rem",
                    right: "1.2rem",
                    width: "28px",
                    height: "28px",
                    borderRadius: "50%",
                    backgroundColor: step.accent,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    opacity: 0.55,
                  }}
                >
                  <span
                    style={{
                      fontFamily: "'Nunito', sans-serif",
                      color: "#fff",
                      fontWeight: 800,
                      fontSize: "0.75rem",
                    }}
                  >
                    {i + 1}
                  </span>
                </div>

                {/* Icon circle */}
                <div
                  style={{
                    width: "72px",
                    height: "72px",
                    borderRadius: "50%",
                    backgroundColor: "var(--lp-bg-primary)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <Icon size={32} color={step.accent} strokeWidth={2} />
                </div>

                <h3
                  style={{
                    fontFamily: "'Nunito', sans-serif",
                    color: "var(--lp-text-dark)",
                    fontWeight: 800,
                    fontSize: "1.15rem",
                  }}
                >
                  {step.title}
                </h3>

                <p
                  style={{
                    fontFamily: "'Nunito', sans-serif",
                    color: "var(--lp-text-heading)",
                    fontWeight: 500,
                    fontSize: "0.98rem",
                    lineHeight: 1.6,
                  }}
                >
                  {step.text}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
