import { useState } from "react";
import { Menu, X } from "lucide-react";
import { useNavigate } from "react-router";
import ThemeToggle from "./ThemeToggle";

export type DashboardNavItem = {
  label: string;
  action: "navigate" | "scroll";
  target: string;
  active?: boolean;
};

// ── Preset nav configs ────────────────────────────────────────────────────────
export const DASHBOARD_NAV: DashboardNavItem[] = [
  { label: "Home",  action: "navigate", target: "/" },
  { label: "About", action: "scroll",   target: "about" },
];

export const SIMULATOR_NAV: DashboardNavItem[] = [
  { label: "Home",  action: "navigate", target: "/" },
  { label: "About", action: "scroll",   target: "about" },
];

// ── Component ─────────────────────────────────────────────────────────────────
export function DashboardHeader({
  navItems = DASHBOARD_NAV,
}: {
  navItems?: DashboardNavItem[];
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleClick = (item: DashboardNavItem) => {
    setMenuOpen(false);
    if (item.action === "navigate") {
      navigate(item.target);
    } else {
      const el = document.getElementById(item.target);
      if (el) el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <header
      className="w-full sticky top-0 z-50 backdrop-blur-[12px]"
      style={{
        backgroundColor: "var(--lp-header-bg)",
        borderBottom: "1px solid rgba(168,190,131,0.2)",
      }}
    >
      <div className="max-w-screen-xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo + Brand */}
        <div className="flex items-center gap-3">
          <img
            src="/src/LOGO.png"
            alt="GPA Goes Logo"
            width={80}
            height={80}
            className="rounded-xl"
          />
          <span
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-dark)",
              fontSize: "1.875rem",
              fontWeight: 800,
            }}
          >
            GPA Goes 📈
          </span>
        </div>

        <div className="flex items-center gap-4">
          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navItems.map((item) => (
              <button
                key={item.label}
                onClick={() => handleClick(item)}
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: item.active ? "var(--lp-text-dark)" : "var(--lp-text-heading)",
                  fontWeight: item.active ? 700 : 600,
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "1rem",
                  transition: "color 0.2s",
                  position: "relative",
                  paddingBottom: "4px",
                }}
                onMouseEnter={(e) => {
                  if (!item.active) e.currentTarget.style.color = "var(--lp-text-dark)";
                }}
                onMouseLeave={(e) => {
                  if (!item.active) e.currentTarget.style.color = "var(--lp-text-heading)";
                }}
              >
                {item.label}
                {item.active && (
                  <span
                    style={{
                      position: "absolute",
                      bottom: 0,
                      left: 0,
                      right: 0,
                      height: "2.5px",
                      backgroundColor: "#A8BE83",
                      borderRadius: "9999px",
                    }}
                  />
                )}
              </button>
            ))}
          </nav>

          <ThemeToggle />

          {/* Mobile Hamburger */}
          <button
            className="md:hidden p-2 rounded-xl"
            style={{ color: "var(--lp-text-heading)" }}
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X size={26} /> : <Menu size={26} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div
          className="md:hidden px-6 pb-5 flex flex-col gap-4"
          style={{ backgroundColor: "var(--lp-bg-primary)" }}
        >
          {navItems.map((item) => (
            <button
              key={item.label}
              onClick={() => handleClick(item)}
              style={{
                fontFamily: "'Nunito', sans-serif",
                color: item.active ? "var(--lp-text-dark)" : "var(--lp-text-heading)",
                fontWeight: item.active ? 700 : 600,
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: "1rem",
                textAlign: "left",
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
}
