import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from 'stores/authStore';

// ==============================|| PROTECTED ROUTE ||============================== //

const ProtectedRoute = ({ children }) => {
  const { token } = useAuthStore();
  const location = useLocation();

  if (!token) {
    // Redirect them to the /login page, but save the current location they were
    // trying to go to. This allows us to send them along to that page after they
    // log in, which is a nicer user experience than dropping them off on the home page.
    return <Navigate to="/pages/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
