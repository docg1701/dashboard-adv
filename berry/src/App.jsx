import { RouterProvider } from 'react-router-dom';
import { SnackbarProvider, useSnackbar } from 'notistack';
import { useEffect } from 'react';

// routing
import router from 'routes';

// project imports
import NavigationScroll from 'layout/NavigationScroll';
import ThemeCustomization from 'themes';
import { useNotificationStore } from 'stores/notificationStore';
import { useAuthStore } from 'stores/authStore';

// ==============================|| NOTIFICATION SETUP ||============================== //

const NotificationSetup = () => {
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const storeSetEnqueueSnackbar = useNotificationStore((state) => state.setEnqueueSnackbar);
  const storeSetCloseSnackbar = useNotificationStore((state) => state.setCloseSnackbar);

  useEffect(() => {
    storeSetEnqueueSnackbar(enqueueSnackbar);
    storeSetCloseSnackbar(closeSnackbar);
  }, [enqueueSnackbar, closeSnackbar, storeSetEnqueueSnackbar, storeSetCloseSnackbar]);

  return null; // This component does not render anything
};

// ==============================|| APP ||============================== //

export default function App() {
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <ThemeCustomization>
      <SnackbarProvider
        maxSnack={5}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        autoHideDuration={3000}
      >
        <NotificationSetup />
        <NavigationScroll>
          <>
            <RouterProvider router={router} />
          </>
        </NavigationScroll>
      </SnackbarProvider>
    </ThemeCustomization>
  );
}
