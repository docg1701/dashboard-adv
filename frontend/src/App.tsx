import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Outlet } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { SnackbarProvider, useSnackbar } from 'notistack';
import theme from './styles/theme';
// Lazy loaded components
const MainLayout = React.lazy(() => import('./layouts/MainLayout'));
const Login = React.lazy(() => import('./components/Login').then(module => ({ default: module.Login })));
const AdminUsers = React.lazy(() => import('./components/AdminUsers'));
const HomePage = React.lazy(() => import('./pages/HomePage'));
const AnalisadorDocumentosPage = React.lazy(() => import('./pages/AnalisadorDocumentosPage'));

import { ProtectedRoute } from './components/ProtectedRoute';
import { getModuleRegistry, ModuleConfig } from './config/moduleRegistry'; // Ensure correct path
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { useNotificationStore } from './stores/notificationStore';
import { useAuthStore } from './stores/authStore'; // Import useAuthStore

// Small component to bridge notistack's context with Zustand store
const NotificationSetup: React.FC = () => {
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  // TODO: Ensure setEnqueueSnackbar and setCloseSnackbar are correctly defined in the store
  // For now, assuming they exist as per the previous subtask's example.
  const setEnqueueSnackbar = useNotificationStore((state) => state.setEnqueueSnackbar);
  const setCloseSnackbar = useNotificationStore((state) => state.setCloseSnackbar);

  useEffect(() => {
    setEnqueueSnackbar(enqueueSnackbar);
    setCloseSnackbar(closeSnackbar);
  }, [enqueueSnackbar, closeSnackbar, setEnqueueSnackbar, setCloseSnackbar]);

  return null; // This component does not render anything
};

function App() {
  const moduleRegistry = getModuleRegistry();
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth(); // Call it on app mount
  }, [initializeAuth]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {/* AuthProvider was removed from here */}
      <SnackbarProvider
        maxSnack={5}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          autoHideDuration={3000}
        >
          <NotificationSetup /> {/* Initialize store with notistack functions */}
          <Router>
            <Suspense fallback={
              <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
                <CircularProgress />
              </Box>
            }>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <MainLayout>
                        <Outlet /> {/* Child routes will render here via MainLayout */}
                      </MainLayout>
                    </ProtectedRoute>
                  }
                >
                  <Route index element={<HomePage />} />
                  <Route path="admin/users" element={<ProtectedRoute roles={['admin']}><AdminUsers /></ProtectedRoute>} />
                  <Route path="analisador-documentos" element={<AnalisadorDocumentosPage />} />
                  {/* Dynamic module routes */}
                  {Object.values(moduleRegistry).map((module: ModuleConfig) =>
                    module.routes.map((route) => (
                      <Route
                        key={`${module.basePath}${route.path}`}
                        path={`${module.basePath}${route.path === '/' ? '' : route.path}`} // Handle base path and nested root
                        element={
                          // ProtectedRoute here now also benefits from SnackbarProvider context
                          <ProtectedRoute adminOnly={module.adminOnly} roles={route.roles}>
                            <route.component />
                          </ProtectedRoute>
                        }
                      />
                    ))
                  )}
                </Route>
              </Routes>
            </Suspense>
          </Router>
        </SnackbarProvider>
      {/* AuthProvider was removed from here */}
    </ThemeProvider>
  );
}

export default App;
