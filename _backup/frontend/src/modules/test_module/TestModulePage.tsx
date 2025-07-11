import React from 'react';
import { Container, Typography, Paper } from '@mui/material';

const TestModulePage: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Test Module Page
        </Typography>
        <Typography variant="body1">
          This is a simple page for the Test Module. If you can see this,
          the dynamic module loading, routing, and navigation are working!
        </Typography>
      </Paper>
    </Container>
  );
};

export default TestModulePage;
