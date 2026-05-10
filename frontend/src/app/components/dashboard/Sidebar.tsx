import { LayoutDashboard, Calculator, Target, BarChart2, BookOpen, Library } from "lucide-react";
import { useNavigate } from "react-router";

export type ActivePage = "dashboard" | "recommendations" | "simulator" | "planner" | "calculator" | "remaining";

type SidebarItem = {
  id: string;
  icon: React.ElementType;
  label: string;
  page?: ActivePage;
  comingSoon?: boolean;
};

const ITEMS: SidebarItem[] = [
  { id: "dashboard",       icon: LayoutDashboard, label: "Dashboard",              page: "dashboard"       },
  { id: "remaining",       icon: Library,          label: "All Remaining Courses",  page: "remaining"       },
  { id: "recommendations", icon: BookOpen,         label: "Course Recommendations", page: "recommendations" },
  { id: "simulator",       icon: BarChart2,        label: "GPA Simulator",          page: "simulator"       },
  { id: "planner",         icon: Target,           label: "Target GPA Planner",     page: "planner"         },
  { id: "calc",            icon: Calculator,       label: "GPA Calculators",        page: "calculator"      },
];

const PAGE_ROUTES: Record<ActivePage, string> = {
  dashboard:       "/dashboard",
  recommendations: "/recommendations",
  simulator:       "/simulator",
  planner:         "/planner",
  calculator:      "/calculator",
  remaining:       "/remaining-courses",
};

export function Sidebar({ activePage = "dashboard" }: { activePage?: ActivePage }) {
  const navigate = useNavigate();

  return (
    <aside
      className="hidden lg:flex flex-col"
      style={{
        width: "256px",
        minWidth: "256px",
        backgroundColor: "var(--lp-bg-secondary)",
        borderRight: "1px solid rgba(168,190,131,0.25)",
        position: "sticky",
        top: "72px",
        height: "calc(100vh - 72px)",
        overflowY: "hidden",
        padding: "1rem 1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.25rem",
      }}
    >
      {ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = item.page === activePage;

        return (
          <div key={item.id} style={{ position: "relative" }}>
            <button
              onClick={() => {
                if (item.comingSoon) return;
                if (item.page) navigate(PAGE_ROUTES[item.page]);
              }}
              style={{
                fontFamily: "'Nunito', sans-serif",
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                padding: "0.75rem 1rem",
                borderRadius: "0.875rem",
                border: "none",
                cursor: item.comingSoon ? "default" : "pointer",
                backgroundColor: isActive ? "#A8BE83" : "transparent",
                color: isActive ? "#ffffff" : item.comingSoon ? "var(--lp-text-heading)" : "var(--lp-text-heading)",
                fontWeight: isActive ? 700 : 600,
                fontSize: "0.95rem",
                textAlign: "left",
                transition: "background-color 0.2s, color 0.2s",
                opacity: item.comingSoon ? 0.7 : 1,
              }}
              onMouseEnter={(e) => {
                if (!isActive && !item.comingSoon) {
                  e.currentTarget.style.backgroundColor = "var(--lp-bg-primary)";
                  e.currentTarget.style.color = "var(--lp-text-dark)";
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive && !item.comingSoon) {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color = "var(--lp-text-heading)";
                }
              }}
            >
              <Icon
                size={18}
                strokeWidth={2}
                color={isActive ? "#fff" : "var(--lp-text-heading)"}
              />
              <span style={{ flex: 1 }}>{item.label}</span>
            </button>

            {item.comingSoon && (
              <span
                style={{
                  position: "absolute",
                  top: "50%",
                  right: "0.75rem",
                  transform: "translateY(-50%)",
                  fontFamily: "'Nunito', sans-serif",
                  fontSize: "0.6rem",
                  fontWeight: 700,
                  color: "var(--lp-text-heading)",
                  backgroundColor: "#F2C27F",
                  padding: "2px 7px",
                  borderRadius: "9999px",
                  letterSpacing: "0.04em",
                  textTransform: "uppercase",
                  pointerEvents: "none",
                }}
              >
                Soon
              </span>
            )}
          </div>
        );
      })}

      <div style={{ flex: 1 }} />

      <div
        style={{
          backgroundColor: "var(--lp-bg-primary)",
          borderRadius: "1rem",
          padding: "1.6rem",
          textAlign: "center",
        }}
      >
        <span style={{ fontSize: "1.8rem" }}>📈</span>
        <p
          style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-heading)",
            fontWeight: 600,
            fontSize: "0.8rem",
            marginTop: "0.4rem",
            lineHeight: 1.4,
          }}
        >
          Keep pushing — your GPA is on the rise!
        </p>
      </div>
    </aside>
  );
}
