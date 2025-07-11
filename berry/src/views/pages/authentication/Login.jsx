import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

// material-ui
import useMediaQuery from '@mui/material/useMediaQuery';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

// project imports
import AuthWrapper1 from './AuthWrapper1';
import AuthCardWrapper from './AuthCardWrapper';
import AuthLogin from './auth-forms/AuthLogin'; // Adjusted path
import Logo from 'ui-component/Logo';
import AuthFooter from 'ui-component/cards/AuthFooter';
import { useAuthStore } from 'stores/authStore';

// ================================|| AUTH - LOGIN ||================================ //

export default function Login() {
  const theme = useMediaQuery((theme) => theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const { token } = useAuthStore();

  useEffect(() => {
    // If a token exists, the user is logged in, so redirect to the dashboard.
    if (token) {
      navigate('/', { replace: true });
    }
  }, [token, navigate]);

  // If token exists, this component will redirect, so we can return null
  // to avoid rendering the login form for a split second.
  if (token) {
    return null;
  }

  return (
    <AuthWrapper1>
      <Grid container direction="column" sx={{ justifyContent: 'flex-end', minHeight: '100vh' }}>
        <Grid item xs={12}>
          <Grid container sx={{ justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 68px)' }}>
            <Grid item sx={{ m: { xs: 1, sm: 3 }, mb: 0 }}>
              <AuthCardWrapper>
                <Grid container spacing={2} sx={{ alignItems: 'center', justifyContent: 'center' }}>
                  <Grid item xs={12}>
                    <Grid container direction="column" sx={{ alignItems: 'center', justifyContent: 'center' }}>
                      <Grid item sx={{ mb: 4 }}>
                        <Link to="#" aria-label="logo">
                          <Logo />
                        </Link>
                      </Grid>
                    </Grid>
                  </Grid>
                  <Grid item xs={12}>
                    <AuthLogin />
                  </Grid>
                </Grid>
              </AuthCardWrapper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </AuthWrapper1>
  );
}