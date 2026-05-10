// @ts-ignore: Allow importing CSS side-effect file without type declarations
import "../styles/fonts.css";
import { RouterProvider } from "react-router";
import { router } from "./routes";
import { AppDataProvider } from "./context/AppDataContext";

export default function App() {
  return (
    <AppDataProvider>
      <RouterProvider router={router} />
    </AppDataProvider>
  );
}
