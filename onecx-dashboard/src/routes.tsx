import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAdmin, RequireAuth } from "@/components/layout/RouteGuards";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { LoginPage } from "@/pages/auth/LoginPage";
import { TrafficPage } from "@/pages/traffic/TrafficPage";
import { InteractionsPage } from "@/pages/interactions/InteractionsPage";
import { JourneyPage } from "@/pages/journey/JourneyPage";
import { EngagementConversionPage } from "@/pages/engagement/EngagementConversionPage";
import { DropoffGroupPage } from "@/pages/dropoff-explorer/DropoffGroupPage";
import { AdminPage } from "@/pages/admin/AdminPage";
import { AccountPage } from "@/pages/account/AccountPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <DashboardShell />
          </RequireAuth>
        }
      >
        <Route index element={<TrafficPage />} />
        <Route path="interactions" element={<InteractionsPage />} />
        <Route path="journey" element={<JourneyPage />} />
        <Route path="journey/:anonymousId" element={<JourneyPage />} />
        <Route path="engagement" element={<EngagementConversionPage />} />
        <Route path="dropoff" element={<DropoffGroupPage />} />
        <Route path="account" element={<AccountPage />} />
        <Route
          path="admin"
          element={
            <RequireAdmin>
              <AdminPage />
            </RequireAdmin>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
