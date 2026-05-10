import { Github, Mail, MessageCircle } from "lucide-react";

const contacts = [
  { icon: Github,        label: "GitHub",  href: "#" },
  { icon: Mail,          label: "Email",   href: "#" },
  { icon: MessageCircle, label: "Discord", href: "#" },
];

export function AboutSection() {
  return (
    <section
      id="about"
      style={{ backgroundColor: "var(--lp-bg-secondary)" }}
      className="w-full py-20 px-6"
    >
      <div className="max-w-2xl mx-auto text-center flex flex-col items-center gap-7">
        {/* Title */}
        <div>
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
            Who We Are
          </p>
          <h2
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--lp-text-heading)",
              fontWeight: 800,
              fontSize: "2rem",
            }}
          >
            About Us
          </h2>
        </div>

        {/* Decorative divider */}
        <div
          style={{
            width: "60px",
            height: "4px",
            borderRadius: "9999px",
            background: "linear-gradient(90deg, #A8BE83, #F2C27F)",
          }}
        />

        {/* About text */}
        <p
          style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-dark)",
            fontWeight: 500,
            fontSize: "1.07rem",
            lineHeight: 1.8,
          }}
        >
          We are students who walked the exact same path you are on right now. We decided to make
          our graduation project a tool that helps you navigate your academic journey with clarity,
          make informed choices, and watch your "GPA Goes 📈".
        </p>

        {/* Contact Links */}
        <div className="flex items-center justify-center gap-8 flex-wrap mt-2">
          {contacts.map(({ icon: Icon, label, href }) => (
            <a
              key={label}
              href={href}
              style={{
                fontFamily: "'Nunito', sans-serif",
                color: "#A8BE83",
                fontWeight: 700,
                fontSize: "1rem",
                display: "flex",
                alignItems: "center",
                gap: "0.45rem",
                textDecoration: "none",
                transition: "color 0.2s, transform 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "var(--lp-text-heading)";
                e.currentTarget.style.transform = "translateY(-2px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "#A8BE83";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <Icon size={18} strokeWidth={2.2} />
              {label}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
