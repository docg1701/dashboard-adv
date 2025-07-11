// frontend/src/pages/PaginaImpugnacaoLaudo.tsx
import React from 'react';
import { Container, Paper, Box, Typography } from '@mui/material';
import ImpugnacaoLaudo from '../modules/impugnacao_laudo/ImpugnacaoLaudo';

const PaginaImpugnacaoLaudo: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" sx={{ mt: 4, mb: 3 }}>
        Impugnação de Laudo Pericial
      </Typography>
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 4 } }}>
        <Box>
          <ImpugnacaoLaudo />
        </Box>
      </Paper>
    </Container>
  );
};

export default PaginaImpugnacaoLaudo;
