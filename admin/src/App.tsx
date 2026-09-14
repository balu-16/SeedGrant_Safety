import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { SosFeedProvider } from "./hooks/useSosFeed";
import { Spinner } from "./components/ui";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import LiveSOS from "./pages/LiveSOS";
import Users from "./pages/Users";
import Devices from "./pages/Devices";
import Guardians from "./pages/Guardians";
import Emergencies from "./pages/Emergencies";
import Locations from "./pages/Locations";
import Push from "./pages/Push";
import Audit from "./pages/Audit";
import System from "./pages/System";

function Splash() {
  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
      <Spinner />
    </div>
  );
}

function Shell() {
  const { admin, booting } = useAuth();
  // Hold the current URL while the session restores — navigating to the login
  // route here would clobber deep links like /live-sos.
  if (booting) return <Splash />;
  if (admin)
    return (
      <SosFeedProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="/live-sos" element={<LiveSOS />} />
            <Route path="/users" element={<Users />} />
            <Route path="/devices" element={<Devices />} />
            <Route path="/guardians" element={<Guardians />} />
            <Route path="/emergencies" element={<Emergencies />} />
            <Route path="/locations" element={<Locations />} />
            <Route path="/push" element={<Push />} />
            <Route path="/audit" element={<Audit />} />
            <Route path="/system" element={<System />} />
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </SosFeedProvider>
    );
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
