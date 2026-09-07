import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles/globals.css";
import { applyTheme } from "./pages/Settings";

// Apply saved theme before first render
applyTheme(localStorage.getItem("theme") || "dark");

createRoot(document.getElementById("root")).render(
  <StrictMode><App /></StrictMode>
);
