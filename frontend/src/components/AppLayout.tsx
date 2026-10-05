import { Link, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

export default function AppLayout() {
  const { user, loading, logout } = useAuth();

  if (loading) return <div className="page">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Link to="/orders">Loading Sheet</Link>
          <span className="badge">{user.role}</span>
        </div>
        <nav>
          <Link to="/orders">Orders</Link>
          <Link to="/orders/new">New order</Link>
          {user.can_market_visit ? (
            <Link to="/market-visit">Market Visit</Link>
          ) : null}
        </nav>
        <div className="user-chip">
          <span>{user.first_name || user.username}</span>
          <button type="button" className="btn" onClick={() => logout()}>
            Log out
          </button>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
