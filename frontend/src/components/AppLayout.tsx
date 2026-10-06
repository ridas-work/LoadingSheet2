import { Link, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

export default function AppLayout() {
  const { user, loading, logout } = useAuth();

  if (loading) return <div className="page">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;

  const isBatchClerk = user.role === "batch_clerk";
  const home = isBatchClerk ? "/batches" : "/orders";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Link to={home}>Loading Sheet</Link>
          <span className="badge">{user.role}</span>
        </div>
        <nav>
          {isBatchClerk ? (
            <>
              <Link to="/batches">Active batches</Link>
              <Link to="/batches/new">New batch</Link>
              <Link to="/packaging">Packaging</Link>
            </>
          ) : (
            <>
              <Link to="/orders">Orders</Link>
              <Link to="/orders/new">New order</Link>
              {user.can_market_visit ? (
                <Link to="/market-visit">Market Visit</Link>
              ) : null}
            </>
          )}
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
