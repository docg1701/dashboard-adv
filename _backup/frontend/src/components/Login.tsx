// frontend/src/components/Login.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TextField, Button, Box, Typography, Container, Alert } from '@mui/material';
import { useAuthStore } from '../stores/authStore';
import { showSuccess, showError } from '../stores/notificationStore'; // Import notification helpers

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState(''); // Renamed to avoid conflict with notification showError
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(''); // Clear previous local errors
    try {
      await login(email, password);
      showSuccess('Login bem-sucedido! Redirecionando...'); // Show success notification
      navigate('/');
    } catch (err: any) { // Added type any to err for accessing response properties
      const errorMessage = err.response?.data?.detail || err.message || 'Falha no login. Verifique suas credenciais ou tente novamente.';
      showError(errorMessage); // Show error notification
      setFormError(errorMessage); // Also set local error if needed for display within the form
    }
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography variant="h5">Login</Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          <TextField
            margin="normal"
            required
            fullWidth
            label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
          />
          <TextField
            margin="normal"
            required
            fullWidth
            label="Senha"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {formError && <Alert severity="error" sx={{ mt: 2 }}>{formError}</Alert>}
          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }}>
            Entrar
          </Button>
        </Box>
      </Box>
    </Container>
  );
};
