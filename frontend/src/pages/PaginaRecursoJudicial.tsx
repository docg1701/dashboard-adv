// frontend/src/pages/PaginaRecursoJudicial.tsx
import React from 'react';
import { Container, Paper, Box, Typography } from '@mui/material';
import RecursoJudicial from '../modules/recurso_judicial/RecursoJudicial';

const PaginaRecursoJudicial: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" sx={{ mt: 4, mb: 3 }}>
        Recurso Judicial
      </Typography>
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 4 } }}>
        <Box>
          <RecursoJudicial />
        </Box>
      </Paper>
    </Container>
  );
};

export default PaginaRecursoJudicial;
