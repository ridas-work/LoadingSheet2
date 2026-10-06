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
import PackagingInventoryPage from "./pages/packaging/PackagingInventory";
import DispatchOrdersPage from "./pages/dispatch/DispatchOrders";
import TripFormPage from "./pages/dispatch/TripForm";
import TripListPage from "./pages/dispatch/TripList";
import LoadingSheetPage from "./pages/loading/LoadingSheet";
import PendingOrdersPage from "./pages/loading/PendingOrders";
import ReadyStockPage from "./pages/loading/ReadyStock";
import LoadingTripDetailPage from "./pages/loading/TripDetail";
import LoadingTripListPage from "./pages/loading/TripList";
import { homeForRole } from "./roleHome";

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={homeForRole(user.role)} replace />;
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
          <Route path="/packaging" element={<PackagingInventoryPage />} />
          <Route path="/dispatch" element={<DispatchOrdersPage />} />
          <Route path="/dispatch/trips" element={<TripListPage />} />
          <Route path="/dispatch/trips/new" element={<TripFormPage />} />
          <Route path="/dispatch/trips/:id" element={<TripFormPage />} />
          <Route path="/loading" element={<LoadingTripListPage />} />
          <Route path="/loading/pending" element={<PendingOrdersPage />} />
          <Route path="/loading/ready-stock" element={<ReadyStockPage />} />
          <Route path="/loading/trips/:id" element={<LoadingTripDetailPage />} />
          <Route
            path="/loading/trips/:id/sheet"
            element={<LoadingSheetPage />}
          />
        </Route>
        <Route path="*" element={<HomeRedirect />} />
      </Routes>
    </AuthProvider>
  );
}
