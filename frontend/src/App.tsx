import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth";
import AppLayout from "./components/AppLayout";
import LoginPage from "./pages/Login";
import MarketVisitFormPage from "./pages/MarketVisitForm";
import MarketVisitListPage from "./pages/MarketVisitList";
import OrderCreatePage from "./pages/OrderCreate";
import OrderDetailPage from "./pages/OrderDetail";
import OrdersListPage from "./pages/OrdersList";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/orders" replace />} />
          <Route path="/orders" element={<OrdersListPage />} />
          <Route path="/orders/new" element={<OrderCreatePage />} />
          <Route path="/orders/:id" element={<OrderDetailPage />} />
          <Route path="/market-visit" element={<MarketVisitListPage />} />
          <Route path="/market-visit/new" element={<MarketVisitFormPage />} />
          <Route path="/market-visit/:id" element={<MarketVisitFormPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/orders" replace />} />
      </Routes>
    </AuthProvider>
  );
}
