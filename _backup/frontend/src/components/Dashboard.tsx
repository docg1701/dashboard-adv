import { Button, Typography, Container } from '@mui/material';
import { useAuthStore } from '../stores/authStore';
import { useNavigate } from 'react-router-dom';

export const Dashboard = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Container>
      <Typography variant="h4" sx={{ mt: 4 }}>Bem-vindo, {user?.email}</Typography>
      <Button variant="contained" onClick={handleLogout} sx={{ mt: 2 }}>
        Sair
      </Button>
    </Container>
  );
};
