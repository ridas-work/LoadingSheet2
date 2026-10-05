import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import AppLayout from "./components/AppLayout";
import LoginPage from "./pages/Login";
import MarketVisitFormPage from "./pages/MarketVisitForm";
import MarketVisitListPage from "./pages/MarketVisitList";
import OrderCreatePage from "./pages/OrderCreate";
import OrderDetailPage from "./pages/OrderDetail";
import OrdersListPage from "./pages/OrdersList";
import BatchFormPage from "./pages/batches/BatchForm";
import BatchListPage from "./pages/batches/BatchList";

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "batch_clerk") return <Navigate to="/batches" replace />;
  return <Navigate to="/orders" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/orders" element={<OrdersListPage />} />
          <Route path="/orders/new" element={<OrderCreatePage />} />
          <Route path="/orders/:id" element={<OrderDetailPage />} />
          <Route path="/market-visit" element={<MarketVisitListPage />} />
          <Route path="/market-visit/new" element={<MarketVisitFormPage />} />
          <Route path="/market-visit/:id" element={<MarketVisitFormPage />} />
          <Route path="/batches" element={<BatchListPage />} />
          <Route path="/batches/new" element={<BatchFormPage />} />
          <Route path="/batches/:id" element={<BatchFormPage />} />
        </Route>
        <Route path="*" element={<HomeRedirect />} />
      </Routes>
    </AuthProvider>
  );
}
