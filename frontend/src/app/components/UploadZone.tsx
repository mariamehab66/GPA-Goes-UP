import { useState, useRef } from "react";
import { FileText, CloudUpload, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router";
import { apiUrl } from "@/lib/api";

export function UploadZone() {
  const [dragging,    setDragging]    = useState(false);
  const [file,        setFile]        = useState<File | null>(null);
  const [semester,    setSemester]    = useState<string>("");
  const [uploading,   setUploading]   = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const fileName = file?.name ?? null;

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) { setFile(dropped); setUploadError(null); }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0];
    if (picked) { setFile(picked); setUploadError(null); }
  };

  const handleSubmit = async () => {
    if (!file || !semester) return;
    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(apiUrl("/api/upload"), { method: "POST", body: formData });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error ?? "Upload failed. Please try again.");
      }
      navigate("/processing", { state: { semester, fileName: file.name } });
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <section
      id="upload"
      style={{ backgroundColor: "var(--lp-bg-secondary)" }}
      className="w-full py-20 px-6"
    >
      <div className="max-w-2xl mx-auto text-center">
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
          Quick & Secure
        </p>
        <h2
          style={{
            fontFamily: "'Nunito', sans-serif",
            color: "var(--lp-text-heading)",
            fontWeight: 800,
            fontSize: "2rem",
            marginBottom: "2.5rem",
          }}
        >
          Upload Your Academic Record
        </h2>

        {/* Drop Card */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          style={{
            backgroundColor: "var(--lp-bg-card)",
            borderRadius: "1.75rem",
            border: `3px dashed ${dragging ? "#9CA35A" : "#A8BE83"}`,
            padding: "3.5rem 2.5rem",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "1.25rem",
            transition: "border-color 0.2s, transform 0.2s",
            transform: dragging ? "scale(1.02)" : "scale(1)",
            boxShadow: dragging
              ? "0 12px 40px rgba(168,190,131,0.3)"
              : "0 8px 32px rgba(79,83,33,0.09)",
          }}
        >
          {/* Icon */}
          <div
            style={{
              width: "80px",
              height: "80px",
              backgroundColor: dragging ? "#C2D0B9" : "var(--lp-bg-secondary)",
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background-color 0.2s",
            }}
          >
            {fileName ? (
              <FileText size={38} color="#A8BE83" strokeWidth={1.8} />
            ) : (
              <CloudUpload size={38} color="#A8BE83" strokeWidth={1.8} />
            )}
          </div>

          {/* Text */}
          {fileName ? (
            <div>
              <p
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--lp-text-dark)",
                  fontWeight: 700,
                  fontSize: "1.1rem",
                }}
              >
                ✅ {fileName}
              </p>
              <p
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--lp-text-accent)",
                  fontWeight: 600,
                  fontSize: "0.9rem",
                  marginTop: "0.3rem",
                }}
              >
                Ready to analyze!
              </p>
            </div>
          ) : (
            <p
              style={{
                fontFamily: "'Nunito', sans-serif",
                color: "var(--lp-text-heading)",
                fontWeight: 700,
                fontSize: "1.2rem",
                textAlign: "center",
              }}
            >
              Drop your Academic Record (PDF) here
            </p>
          )}

          {/* Browse Button */}
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            style={{ display: "none" }}
          />
          <button
            onClick={() => inputRef.current?.click()}
            style={{
              fontFamily: "'Nunito', sans-serif",
              backgroundColor: "#A8BE83",
              color: "#ffffff",
              fontWeight: 700,
              fontSize: "1rem",
              padding: "0.8rem 2.5rem",
              borderRadius: "9999px",
              border: "none",
              cursor: "pointer",
              boxShadow: "0 4px 16px rgba(168,190,131,0.4)",
              marginTop: "0.25rem",
              transition: "transform 0.15s, box-shadow 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = "0 8px 20px rgba(168,190,131,0.5)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 4px 16px rgba(168,190,131,0.4)";
            }}
          >
            Browse Files
          </button>

          {/* Semester Dropdown */}
          <div style={{ position: "relative", width: "100%", maxWidth: "260px" }}>
            <select
              value={semester}
              onChange={(e) => setSemester(e.target.value)}
              style={{
                fontFamily: "'Nunito', sans-serif",
                backgroundColor: "var(--lp-bg-secondary)",
                color: semester ? "var(--lp-text-dark)" : "var(--lp-text-heading)",
                fontWeight: 600,
                fontSize: "0.98rem",
                width: "100%",
                padding: "0.75rem 2.8rem 0.75rem 1.4rem",
                borderRadius: "9999px",
                border: "2px solid #A8BE83",
                cursor: "pointer",
                outline: "none",
                appearance: "none",
                WebkitAppearance: "none",
                transition: "border-color 0.2s, box-shadow 0.2s",
                boxShadow: "0 2px 10px rgba(79,83,33,0.07)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "#9CA35A";
                e.currentTarget.style.boxShadow = "0 0 0 3px rgba(168,190,131,0.25)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "#A8BE83";
                e.currentTarget.style.boxShadow = "0 2px 10px rgba(79,83,33,0.07)";
              }}
            >
              <option value="" disabled>Select Semester</option>
              <option value="fall">Fall</option>
              <option value="spring">Spring</option>
              <option value="summer">Summer</option>
            </select>
            {/* Custom chevron arrow */}
            <div
              style={{
                position: "absolute",
                right: "1.1rem",
                top: "50%",
                transform: "translateY(-50%)",
                pointerEvents: "none",
                color: "var(--lp-text-heading)",
                display: "flex",
                alignItems: "center",
              }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path
                  d="M3 5L7 9L11 5"
                  stroke="var(--lp-text-heading)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>

          {/* Submit CTA */}
          {file && semester && (
            <button
              onClick={handleSubmit}
              disabled={uploading}
              style={{
                fontFamily: "'Nunito', sans-serif",
                backgroundColor: uploading ? "#8A9460" : "#4F5321",
                color: "#ffffff",
                fontWeight: 700,
                fontSize: "1rem",
                padding: "0.8rem 2rem",
                borderRadius: "9999px",
                border: "none",
                cursor: uploading ? "not-allowed" : "pointer",
                boxShadow: "0 4px 16px rgba(79,83,33,0.35)",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                transition: "transform 0.15s, box-shadow 0.15s, background-color 0.15s",
              }}
              onMouseEnter={(e) => {
                if (!uploading) {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 8px 22px rgba(79,83,33,0.45)";
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 4px 16px rgba(79,83,33,0.35)";
              }}
            >
              {uploading ? "Uploading…" : <>View My Dashboard <ArrowRight size={16} /></>}
            </button>
          )}

          {/* Inline error message */}
          {uploadError && (
            <p
              style={{
                fontFamily: "'Nunito', sans-serif",
                color: "#C87330",
                fontWeight: 600,
                fontSize: "0.88rem",
                marginTop: "0.25rem",
                textAlign: "center",
                maxWidth: "340px",
                lineHeight: 1.5,
              }}
            >
              ⚠️ {uploadError}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
