import { Link, useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { getUser, logout } from "../auth";

export default function Nav() {
  const nav = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState(() => getUser());

  useEffect(() => {
    setUser(getUser());
  }, [location.pathname]);

  return (
    <div className="nav">
      <div className="nav-inner">
        <Link to="/" className="brand" title="Event Platform">
          <span className="brand-main">EVENT</span>
          <span className="brand-accent">PLATFORM</span>
        </Link>

        <div className="nav-links">
          {!user && <Link to="/login">Login</Link>}
          {!user && <Link to="/register">Register</Link>}

          {user?.role === "organizer" && <Link to="/create-event">Create Event</Link>}
          {user?.role === "participant" && <Link to="/my-registrations">My Registrations</Link>}
          {(user?.role === "organizer" || user?.role === "volunteer") && (
            <Link to="/checkin">Check-in</Link>
          )}
        </div>

        <div className="nav-right">
          {user ? (
            <>
              <span className="badge neon">{user.name} · {user.role}</span>
              <button
                className="btn"
                onClick={() => {
                  logout();
                  setUser(null);
                  nav("/login");
                }}
              >
                Logout
              </button>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
