import { RedirectToSignIn, SignedIn, SignedOut } from "@clerk/clerk-react";
import { Route, Routes } from "react-router-dom";
import { MockRedirectToSignIn, MockSignedIn, MockSignedOut } from "./mockAuth";

import { Sidebar } from "./components/Sidebar";
import Dashboard from "./views/Dashboard";
import Clients from "./views/Clients";
import ClientDetail from "./views/ClientDetail";
import Meetings from "./views/Meetings";
import Learning from "./views/Learning";

function Ambient() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden>
      <div className="orb orb-violet -left-24 -top-24 h-96 w-96" />
      <div className="orb orb-cyan -right-24 top-1/3 h-80 w-80" />
      <div className="orb orb-amber bottom-0 left-1/3 h-72 w-72" />
    </div>
  );
}

function Shell() {
  return (
    <div className="relative min-h-screen">
      <Ambient />
      <Sidebar />
      <main className="relative z-10 ml-16 p-6 lg:ml-56 lg:p-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/clients/:id" element={<ClientDetail />} />
          <Route path="/meetings" element={<Meetings />} />
          <Route path="/learning" element={<Learning />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const MOCK = import.meta.env.VITE_MOCK_AUTH === "true";
  const SignedInEl = MOCK ? MockSignedIn : SignedIn;
  const SignedOutEl = MOCK ? MockSignedOut : SignedOut;
  const RedirectEl = MOCK ? MockRedirectToSignIn : RedirectToSignIn;

  return (
    <>
      <SignedInEl>
        <Shell />
      </SignedInEl>
      <SignedOutEl>
        <RedirectEl />
      </SignedOutEl>
    </>
  );
}
