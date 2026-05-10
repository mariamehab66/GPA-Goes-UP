import { useState } from "react";
import { Menu, X } from "lucide-react";
import { useNavigate } from "react-router";
import ThemeToggle from "./ThemeToggle";

type NavItem = {
  label: string;
  action: "navigate" | "scroll";
  target: string;
};

const navItems: NavItem[] = [
  { label: "Home",                    action: "scroll",   target: "home" },
  { label: "Upload Academic Record",  action: "scroll",   target: "upload" },
  { label: "How It Works",            action: "scroll",   target: "how-it-works" },
  { label: "About",                   action: "scroll",   target: "about" },
];

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleClick = (item: NavItem) => {
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
      className="w-full sticky top-0 z-50 backdrop-blur-[10px]"
      style={{ backgroundColor: "var(--lp-header-bg)" }}
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
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
          <nav className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <button
                key={item.label}
                onClick={() => handleClick(item)}
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--lp-text-heading)",
                  fontWeight: 600,
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "1rem",
                  transition: "color 0.2s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--lp-text-dark)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--lp-text-heading)")}
              >
                {item.label}
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
                color: "var(--lp-text-heading)",
                fontWeight: 600,
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
