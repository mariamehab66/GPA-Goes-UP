export function Footer() {
  return (
    <footer
      style={{ backgroundColor: "var(--lp-footer-bg)" }}
      className="w-full py-8 px-6"
    >
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <span
          className="p-[0px] mx-[65px] my-[0px]"
          style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-footer-text)",
            fontWeight: 700,
            fontSize: "1.1rem",
          }}
        >
          GPA Goes 📈
        </span>
        <p
          style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-footer-subtext)",
            fontWeight: 500,
            fontSize: "0.9rem",
          }}
        >
          Built with ❤️ by students, for students · {new Date().getFullYear()}
        </p>
        <p
          className="px-[30px] py-[0px] p-[0px] mx-[65px] my-[0px]"
          style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-footer-muted)",
            fontWeight: 500,
            fontSize: "0.85rem",
          }}
        >
          Your data stays yours 🔒
        </p>
      </div>
    </footer>
  );
}
