import { createBrowserRouter } from "react-router";
import { LandingPage } from "./pages/LandingPage";
import { DashboardPage } from "./pages/DashboardPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { SimulatorPage } from "./pages/SimulatorPage";
import { PlannerPage } from "./pages/PlannerPage";
import { GPACalculatorPage } from "./pages/GPACalculatorPage";
import { RemainingCoursesPage } from "./pages/RemainingCoursesPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { UploadErrorPage } from "./pages/UploadErrorPage";

export const router = createBrowserRouter([
  { path: "/",                Component: LandingPage },
  { path: "/processing",      Component: ProcessingPage },
  { path: "/error",           Component: UploadErrorPage },
  { path: "/dashboard",       Component: DashboardPage },
  { path: "/recommendations", Component: RecommendationsPage },
  { path: "/simulator",       Component: SimulatorPage },
  { path: "/planner",         Component: PlannerPage },
  { path: "/calculator",        Component: GPACalculatorPage },
  { path: "/remaining-courses", Component: RemainingCoursesPage },
]);