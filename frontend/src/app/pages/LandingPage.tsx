import { Header } from "../components/Header";
import { HeroSection } from "../components/HeroSection";
import { UploadZone } from "../components/UploadZone";
import { HowItWorks } from "../components/HowItWorks";
import { AboutSection } from "../components/AboutSection";
import { Footer } from "../components/Footer";
//import { ChatbotFAB } from "../components/ChatbotFAB";

export function LandingPage() {
  return (
    <div
      className="min-h-screen overflow-x-hidden"
      style={{ fontFamily: "'Nunito', sans-serif" }}
    >
      <Header />
      <main>
        <HeroSection />
        <UploadZone />
        <HowItWorks />
        <AboutSection />
      </main>
      <Footer />
    </div>
  );
}
//    <ChatbotFAB /> before </Footer>