// Dev-only auth mock — VITE_MOCK_AUTH=true swaps Clerk for a fixed identity
// so the glass UI can be rendered/screenshotted without a real Clerk instance.

import { createContext, useContext } from "react";

const Ctx = createContext(null);

export function MockClerkProvider({ children }) {
  const value = {
    user: { primaryEmailAddress: { emailAddress: "demo@aabdm.ai" } },
    getToken: async () => "mock-token",
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function MockSignedIn({ children }) {
  return <>{children}</>;
}

export function MockSignedOut() {
  return null;
}

export function MockUserButton() {
  return (
    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-aurora-violet/30 text-xs font-semibold text-white">
      D
    </div>
  );
}

export function MockRedirectToSignIn() {
  return null;
}

export function useMockAuth() {
  return useContext(Ctx);
}
