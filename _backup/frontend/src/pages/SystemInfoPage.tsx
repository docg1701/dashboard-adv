// frontend/src/pages/SystemInfoPage.tsx
import React from 'react';
import SystemInfoDisplay from '../modules/info/SystemInfoDisplay'; // Import the display component
import { Container, Typography } from '@mui/material'; // Optional: Add page-level elements

const SystemInfoPage: React.FC = () => {
  return (
    <Container maxWidth="md"> {/* Optional: Constrain width */}
      <Typography variant="h4" component="h1" sx={{ my: 3 }}> {/* Optional: Page title */}
        System Status
      </Typography>
      <SystemInfoDisplay />
    </Container>
  );
};

export default SystemInfoPage;