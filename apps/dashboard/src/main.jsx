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
    <BrowserRouter>
      <AuthProvider
        publishableKey={PUBLISHABLE_KEY}
        signInUrl={import.meta.env.VITE_CLERK_SIGN_IN_URL}
        signUpUrl={import.meta.env.VITE_CLERK_SIGN_UP_URL}
      >
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
