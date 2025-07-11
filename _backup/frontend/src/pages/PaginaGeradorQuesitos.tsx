// frontend/src/pages/PaginaGeradorQuesitos.tsx
import React from 'react';
import GeradorQuesitos from '../modules/gerador_quesitos/GeradorQuesitos';
import { Container, Typography } from '@mui/material';

const PaginaGeradorQuesitos: React.FC = () => {
  return (
    // Use Container for consistent padding and max-width
    <Container maxWidth="lg" sx={{ mt: 2, mb: 4 }}>
      {/* Optional: Add a page title if desired */}
      {/* <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Gerador de Quesitos Periciais (PDF)
      </Typography> */}

      {/* Render the main UI component for this module */}
      <GeradorQuesitos />
    </Container>
  );
};

export default PaginaGeradorQuesitos;