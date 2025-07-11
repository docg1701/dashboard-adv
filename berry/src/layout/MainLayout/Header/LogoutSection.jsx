// berry/src/layout/MainLayout/Header/LogoutSection.jsx
import { useNavigate } from 'react-router-dom';
import { useTheme } from '@mui/material/styles';
import { Box, Typography, IconButton, Tooltip } from '@mui/material';
import { IconLogout } from '@tabler/icons-react';
import { useAuthStore } from 'stores/authStore';

const LogoutSection = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/pages/login');
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, ml: 2 }}>
      <Typography variant="subtitle1" sx={{ color: theme.palette.text.primary }}>
        {user?.email || 'Usuário'}
      </Typography>
      <Tooltip title="Sair">
        <IconButton
          onClick={handleLogout}
          sx={{
            color: theme.palette.error.dark,
            bgcolor: theme.palette.error.light,
            '&:hover': {
              bgcolor: theme.palette.error.main,
              color: theme.palette.error.contrastText
            }
          }}
        >
          <IconLogout stroke={1.5} size="20px" />
        </IconButton>
      </Tooltip>
    </Box>
  );
};

export default LogoutSection;
