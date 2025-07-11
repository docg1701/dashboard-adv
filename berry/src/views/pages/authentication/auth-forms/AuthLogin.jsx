import { useState } from 'react';

// material-ui
import { useTheme } from '@mui/material/styles';
import {
  Box,
  Button,
  FormControl,
  FormHelperText,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  OutlinedInput,
  Typography
} from '@mui/material';

// project imports
import AnimateButton from 'ui-component/extended/AnimateButton';
import { useAuthStore } from 'stores/authStore';
import { showSuccess, showError } from 'stores/notificationStore';

// assets
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

// ============================|| LOGIN FORM ||============================ //

const AuthLogin = () => {
  const theme = useTheme();
  const { login, isLoading } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    try {
      await login(email, password);
      // On success, the useEffect in the parent Login.jsx will handle the redirect.
      showSuccess('Login bem-sucedido!');
    } catch (err) {
      const errorMessage = err.message || 'Falha no login. Verifique suas credenciais.';
      showError(errorMessage);
      setFormError(errorMessage);
    }
  };

  return (
    <>
      <form noValidate onSubmit={handleSubmit}>
        <FormControl fullWidth error={!!formError} sx={{ ...theme.typography.customInput }}>
          <InputLabel htmlFor="outlined-adornment-email-login">Endereço de E-mail</InputLabel>
          <OutlinedInput
            id="outlined-adornment-email-login"
            type="email"
            value={email}
            name="email"
            onChange={(e) => setEmail(e.target.value)}
            label="Endereço de E-mail"
            required
          />
        </FormControl>

        <FormControl fullWidth error={!!formError} sx={{ ...theme.typography.customInput }}>
          <InputLabel htmlFor="outlined-adornment-password-login">Senha</InputLabel>
          <OutlinedInput
            id="outlined-adornment-password-login"
            type={showPassword ? 'text' : 'password'}
            value={password}
            name="password"
            onChange={(e) => setPassword(e.target.value)}
            endAdornment={
              <InputAdornment position="end">
                <IconButton
                  aria-label="toggle password visibility"
                  onClick={handleClickShowPassword}
                  onMouseDown={handleMouseDownPassword}
                  edge="end"
                  size="large"
                >
                  {showPassword ? <Visibility /> : <VisibilityOff />}
                </IconButton>
              </InputAdornment>
            }
            label="Senha"
            required
          />
        </FormControl>

        {formError && (
          <Box sx={{ mt: 3 }}>
            <FormHelperText error>{formError}</FormHelperText>
          </Box>
        )}

        <Box sx={{ mt: 2 }}>
          <AnimateButton>
            <Button
              disableElevation
              disabled={isLoading}
              fullWidth
              size="large"
              type="submit"
              variant="contained"
              color="secondary"
            >
              {isLoading ? 'Entrando...' : 'Entrar'}
            </Button>
          </AnimateButton>
        </Box>
      </form>
    </>
  );
};

export default AuthLogin;
