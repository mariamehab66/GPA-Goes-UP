import { useState, useRef, useEffect } from "react";
import { BotMessageSquare, X, Send, Maximize2, Minimize2 } from "lucide-react";
import { useIsMobile } from "./ui/use-mobile";
import { useAppData } from "../context/AppDataContext";
import { apiUrl } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

type Message = {
  role: "user" | "bot";
  text: string;
};

const TOPICS = [
  "Course registration rules",
  "Understanding my GPA",
  "Reading ML recommendations",
  "Simulator results explained",
];

// ── sessionStorage helpers ────────────────────────────────────────────────────

function ssGet(key: string): string | null {
  try { return sessionStorage.getItem(key); } catch { return null; }
}
function ssSet(key: string, value: string) {
  try { sessionStorage.setItem(key, value); } catch { /* ignore */ }
}

// ── Component ─────────────────────────────────────────────────────────────────

export function ChatbotFAB({ pageContext = "" }: { pageContext?: string } = {}) {
  const isMobile = useIsMobile();
  const { appData } = useAppData();

  // All persistent state survives page navigation (cleared when tab is closed)
  const [teaserDismissed, setTeaserDismissed] = useState(() => ssGet("chat_teaser") === "1");
  const [isOpen,          setIsOpen]          = useState(() => ssGet("chat_open")   === "1");
  const [isExpanded,      setIsExpanded]      = useState(() => ssGet("chat_exp")    === "1");
  const [messages,        setMessages]        = useState<Message[]>(() => {
    try { return JSON.parse(ssGet("chat_msgs") ?? "[]"); } catch { return []; }
  });
  const [input,           setInput]           = useState(() => ssGet("chat_input") ?? "");
  const [loading,         setLoading]         = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  const showTeaser = !teaserDismissed && !isOpen;

  // Sync state → sessionStorage
  useEffect(() => { ssSet("chat_teaser", teaserDismissed ? "1" : "0"); }, [teaserDismissed]);
  useEffect(() => { ssSet("chat_open",   isOpen          ? "1" : "0"); }, [isOpen]);
  useEffect(() => { ssSet("chat_exp",    isExpanded      ? "1" : "0"); }, [isExpanded]);
  useEffect(() => { ssSet("chat_msgs",   JSON.stringify(messages));    }, [messages]);
  useEffect(() => { ssSet("chat_input",  input);                       }, [input]);

  // Scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 120);
  }, [isOpen]);

  const handleFABClick = () => {
    setIsOpen(true);
    setTeaserDismissed(true);
  };

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const studentId = appData?.stats?.studentId;
    const semester  = appData?.stats?.semesterHistory?.at(-1)?.sem ?? "fall";

    setMessages(prev => [...prev, { role: "user", text: trimmed }]);
    setInput("");
    setLoading(true);

    try {
      const res  = await fetch(apiUrl("/api/chat"), {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id:   studentId,
          message:      trimmed,
          semester:     semester.toLowerCase().split(" ")[0],
          page_context: pageContext,
        }),
      });
      const json = await res.json();
      setMessages(prev => [
        ...prev,
        {
          role: "bot",
          text: res.ok
            ? (json.response ?? "No response received.")
            : (json.error   ?? "Something went wrong. Please try again."),
        },
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        { role: "bot", text: "Could not reach the advisor. Please check your connection." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const isDisabled  = loading || !appData;
  const placeholder = !appData
    ? "Upload your transcript first…"
    : loading
    ? "Waiting for response…"
    : "Ask about your courses or GPA…";

  // ── Panel geometry ──────────────────────────────────────────────────────────
  // Expanded (desktop): tall right-side panel so the website stays usable alongside it.
  // Compact  (desktop): floating bubble above the FAB, capped to safe viewport height.
  // Mobile expanded / compact: full-width bottom sheet.

  const panelStyle: React.CSSProperties = isExpanded
    ? isMobile
      ? { top: 0, left: 0, right: 0, bottom: 0, width: "100%", borderRadius: 0, maxHeight: "100dvh" }
      : { top: 0, right: 0, bottom: 0, width: "clamp(360px, 34vw, 480px)", borderRadius: 0, maxHeight: "100dvh" }
    : isMobile
      ? { bottom: 0, left: 0, right: 0, width: "100%", borderRadius: "1.25rem 1.25rem 0 0", maxHeight: "80dvh" }
      : { bottom: "calc(1.75rem + 58px + 14px)", right: "1.75rem", width: "340px", borderRadius: "1.25rem", maxHeight: "min(520px, calc(100dvh - 9rem))" };

  // Hide FAB while expanded (panel covers the right side)
  const showFAB = !(isOpen && isExpanded && !isMobile);

  return (
    <>
      <style>{`
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes chatSlideUp {
          from { opacity: 0; transform: translateY(16px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes chatSlideInRight {
          from { opacity: 0; transform: translateX(24px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes dotPulse {
          0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
          40%            { opacity: 1;   transform: scale(1); }
        }
        .chat-dot { animation: dotPulse 1.2s ease-in-out infinite; }
        .chat-dot:nth-child(2) { animation-delay: 0.2s; }
        .chat-dot:nth-child(3) { animation-delay: 0.4s; }
        /* Thin scrollbar inside message list */
        .chat-messages::-webkit-scrollbar { width: 4px; }
        .chat-messages::-webkit-scrollbar-track { background: transparent; }
        .chat-messages::-webkit-scrollbar-thumb { background: #C2D0B9; border-radius: 4px; }
      `}</style>

      {/* ── Teaser bubble ── */}
      {showTeaser && (
        <div style={{
          position: "fixed",
          bottom: "calc(1.75rem + 58px + 14px)",
          right: "1.75rem",
          zIndex: 9998,
          animation: "fadeSlideUp 0.3s ease",
        }}>
          <div style={{
            position: "relative",
            backgroundColor: "var(--lp-bg-card)",
            borderRadius: "1rem",
            padding: "0.875rem 2.25rem 0.875rem 1rem",
            boxShadow: "0 4px 24px rgba(79,83,33,0.13), 0 1px 4px rgba(79,83,33,0.07)",
            border: "1.5px solid var(--lp-bg-secondary)",
            maxWidth: "230px",
          }}>
            <button
              onClick={() => setTeaserDismissed(true)}
              style={{
                position: "absolute", top: "0.5rem", right: "0.5rem",
                backgroundColor: "transparent", border: "none", cursor: "pointer",
                padding: "2px", display: "flex", alignItems: "center", justifyContent: "center",
                color: "#B8A888", borderRadius: "50%", transition: "color 0.2s",
              }}
              onMouseEnter={e => (e.currentTarget.style.color = "#88734B")}
              onMouseLeave={e => (e.currentTarget.style.color = "#B8A888")}
              aria-label="Dismiss"
            >
              <X size={13} strokeWidth={2.5} />
            </button>
            <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 700, fontSize: "0.85rem", margin: "0 0 0.2rem", lineHeight: 1.4 }}>
              Got a question? 💬
            </p>
            <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-heading)", fontWeight: 500, fontSize: "0.78rem", margin: 0, lineHeight: 1.45 }}>
              Ask me about registration rules, your GPA results, or recommendations.
            </p>
            <div style={{
              position: "absolute", bottom: "-7px", right: "26px",
              width: "14px", height: "14px", backgroundColor: "var(--lp-bg-card)",
              borderRight: "1.5px solid var(--lp-bg-secondary)", borderBottom: "1.5px solid var(--lp-bg-secondary)",
              transform: "rotate(45deg)",
            }} />
          </div>
        </div>
      )}

      {/* ── Chat panel ── */}
      {isOpen && (
        <div style={{
          position: "fixed",
          ...panelStyle,
          backgroundColor: "var(--lp-bg-card)",
          boxShadow: isExpanded
            ? "-6px 0 40px rgba(79,83,33,0.14), -1px 0 0 var(--lp-bg-secondary)"
            : "0 8px 40px rgba(79,83,33,0.18), 0 2px 8px rgba(79,83,33,0.10)",
          border: "1.5px solid var(--lp-bg-secondary)",
          overflow: "hidden",
          zIndex: 9998,
          animation: isExpanded ? "chatSlideInRight 0.25s ease" : "chatSlideUp 0.28s ease",
          display: "flex",
          flexDirection: "column",
        }}>

          {/* ── Header ── */}
          <div style={{
            backgroundColor: "#4F5321",
            padding: "0.875rem 1.1rem",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            flexShrink: 0,
          }}>
            <div style={{
              width: "36px", height: "36px", borderRadius: "50%",
              backgroundColor: "rgba(168,190,131,0.2)",
              border: "1.5px solid rgba(168,190,131,0.35)",
              display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
            }}>
              <BotMessageSquare size={17} color="#A8BE83" strokeWidth={1.75} />
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ fontFamily: "'Nunito', sans-serif", color: "#fff", fontWeight: 800, fontSize: "0.92rem", margin: 0 }}>
                Academic Assistant
              </p>
              <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-footer-subtext)", fontWeight: 500, fontSize: "0.7rem", margin: 0 }}>
                GPA Goes UP · AI Guide
              </p>
            </div>

            {/* Expand / collapse toggle */}
            <button
              onClick={() => setIsExpanded(v => !v)}
              style={{
                backgroundColor: "rgba(255,255,255,0.1)", border: "none", borderRadius: "50%",
                width: "28px", height: "28px", cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background-color 0.2s", flexShrink: 0,
              }}
              onMouseEnter={e => (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.22)")}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.10)")}
              aria-label={isExpanded ? "Collapse chat" : "Expand chat to full panel"}
              title={isExpanded ? "Collapse" : "Expand"}
            >
              {isExpanded
                ? <Minimize2 size={14} color="#fff" strokeWidth={2.5} />
                : <Maximize2 size={14} color="#fff" strokeWidth={2.5} />
              }
            </button>

            {/* Close */}
            <button
              onClick={() => setIsOpen(false)}
              style={{
                backgroundColor: "rgba(255,255,255,0.1)", border: "none", borderRadius: "50%",
                width: "28px", height: "28px", cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background-color 0.2s", flexShrink: 0,
              }}
              onMouseEnter={e => (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.22)")}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.10)")}
              aria-label="Close chat"
            >
              <X size={15} color="#fff" strokeWidth={2.5} />
            </button>
          </div>

          {/* ── Message list ── */}
          <div
            className="chat-messages"
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "1rem 1.1rem 0.5rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.65rem",
            }}
          >
            {/* Welcome bubble */}
            <div style={{
              backgroundColor: "var(--lp-bg-secondary)",
              borderRadius: "0.875rem 0.875rem 0.875rem 0.2rem",
              padding: "0.75rem 0.9rem",
              maxWidth: "88%",
              alignSelf: "flex-start",
            }}>
              <p style={{ fontFamily: "'Nunito', sans-serif", color: "var(--lp-text-dark)", fontWeight: 600, fontSize: "0.85rem", margin: 0, lineHeight: 1.5 }}>
                👋 Hi! I can help you with:
              </p>
            </div>

            {/* Topic chips */}
            {messages.length === 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", paddingLeft: "0.1rem" }}>
                {TOPICS.map(topic => (
                  <button
                    key={topic}
                    onClick={() => sendMessage(topic)}
                    disabled={isDisabled}
                    style={{
                      fontFamily: "'Nunito', sans-serif",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                      color: "var(--lp-text-dark)",
                      backgroundColor: "#F0F6EA",
                      border: "1px solid #C2D0B9",
                      padding: "3px 10px",
                      borderRadius: "9999px",
                      cursor: isDisabled ? "not-allowed" : "pointer",
                      opacity: isDisabled ? 0.6 : 1,
                      transition: "background-color 0.15s",
                    }}
                    onMouseEnter={e => { if (!isDisabled) e.currentTarget.style.backgroundColor = "#DFF0D1"; }}
                    onMouseLeave={e => { e.currentTarget.style.backgroundColor = "#F0F6EA"; }}
                  >
                    {topic}
                  </button>
                ))}
              </div>
            )}

            {/* Conversation */}
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{ alignSelf: msg.role === "user" ? "flex-end" : "flex-start", maxWidth: "88%" }}
              >
                <div style={{
                  backgroundColor: msg.role === "user" ? "#4F5321" : "var(--lp-bg-secondary)",
                  color:           msg.role === "user" ? "#fff"     : "var(--lp-text-dark)",
                  borderRadius: msg.role === "user"
                    ? "0.875rem 0.875rem 0.2rem 0.875rem"
                    : "0.875rem 0.875rem 0.875rem 0.2rem",
                  padding: "0.6rem 0.875rem",
                  fontFamily: "'Nunito', sans-serif",
                  fontSize: "0.83rem",
                  fontWeight: 500,
                  lineHeight: 1.55,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}>
                  {msg.text}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div style={{ alignSelf: "flex-start" }}>
                <div style={{
                  backgroundColor: "var(--lp-bg-secondary)",
                  borderRadius: "0.875rem 0.875rem 0.875rem 0.2rem",
                  padding: "0.65rem 0.9rem",
                  display: "flex",
                  gap: "4px",
                  alignItems: "center",
                }}>
                  {[0, 1, 2].map(i => (
                    <span key={i} className="chat-dot" style={{
                      display: "inline-block",
                      width: "7px",
                      height: "7px",
                      borderRadius: "50%",
                      backgroundColor: "var(--lp-text-heading)",
                    }} />
                  ))}
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* ── Input area ── */}
          <div style={{
            borderTop: "1px solid var(--lp-bg-secondary)",
            padding: "0.75rem 1.1rem",
            display: "flex",
            gap: "0.5rem",
            alignItems: "center",
            backgroundColor: "var(--lp-bg-card)",
            flexShrink: 0,
          }}>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isDisabled}
              placeholder={placeholder}
              style={{
                flex: 1,
                fontFamily: "'Nunito', sans-serif",
                fontSize: "0.83rem",
                color: isDisabled ? "#B8A888" : "#4F5321",
                backgroundColor: "var(--lp-bg-secondary)",
                border: "none",
                borderRadius: "0.625rem",
                padding: "0.55rem 0.85rem",
                outline: "none",
                cursor: isDisabled ? "not-allowed" : "text",
              }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={isDisabled || !input.trim()}
              style={{
                width: "34px",
                height: "34px",
                borderRadius: "0.625rem",
                backgroundColor: isDisabled || !input.trim() ? "var(--lp-bg-primary)" : "#4F5321",
                border: "none",
                cursor: isDisabled || !input.trim() ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                transition: "background-color 0.15s",
              }}
              aria-label="Send"
            >
              <Send size={14} color={isDisabled || !input.trim() ? "#B8A888" : "#fff"} strokeWidth={2} />
            </button>
          </div>
        </div>
      )}

      {/* ── FAB button — hidden while expanded on desktop (panel replaces it) ── */}
      {showFAB && (
        <button
          onClick={handleFABClick}
          aria-label="Open academic assistant"
          style={{
            position: "fixed",
            bottom: "1.75rem",
            right: "1.75rem",
            width: "58px",
            height: "58px",
            borderRadius: "50%",
            backgroundColor: "#4F5321",
            border: "none",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 20px rgba(79,83,33,0.40), 0 1px 6px rgba(79,83,33,0.20)",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
            zIndex: 9999,
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = "scale(1.08)";
            e.currentTarget.style.boxShadow = "0 8px 28px rgba(79,83,33,0.50), 0 2px 8px rgba(79,83,33,0.25)";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = "scale(1)";
            e.currentTarget.style.boxShadow = "0 4px 20px rgba(79,83,33,0.40), 0 1px 6px rgba(79,83,33,0.20)";
          }}
        >
          <BotMessageSquare size={26} color="#fff" strokeWidth={1.75} />
        </button>
      )}
    </>
  );
}
