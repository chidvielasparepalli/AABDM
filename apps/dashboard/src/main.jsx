import React from "react";
import { createRoot } from "react-dom/client";
import { ClerkProvider } from "@clerk/clerk-react";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { MockClerkProvider } from "./mockAuth";
import "./styles.css";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const MOCK = import.meta.env.VITE_MOCK_AUTH === "true";

if (!PUBLISHABLE_KEY && !MOCK) {
  throw new Error(
    "VITE_CLERK_PUBLISHABLE_KEY missing. Copy .env.example to .env and set your Clerk frontend key."
  );
}

const AuthProvider = MOCK ? MockClerkProvider : ClerkProvider;

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider publishableKey={PUBLISHABLE_KEY}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
);
