// frontend/src/pages/PaginaAnaliseDocsMedicos.tsx
import React from 'react';
import { Container, Paper, Box, Typography } from '@mui/material';
import AnaliseDocsMedicos from '../modules/analise_docs_medicos/AnaliseDocsMedicos';

const PaginaAnaliseDocsMedicos: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" sx={{ mt: 4, mb: 3 }}>
        Análise de Documentação Médica
      </Typography>
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 4 } }}>
        <Box>
          <AnaliseDocsMedicos />
        </Box>
      </Paper>
    </Container>
  );
};

export default PaginaAnaliseDocsMedicos;