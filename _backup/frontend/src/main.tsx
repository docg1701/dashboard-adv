// frontend/src/main.tsx
// REMOVED: import React from 'react'; - No longer needed for JSX transform
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import theme from './styles/theme'; // Import our custom theme
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Find the root element
const rootElement = document.getElementById('root');

// Ensure the root element exists before rendering
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    // We are removing React.StrictMode for now to avoid double renders in dev
    // <React.StrictMode>
      <ThemeProvider theme={theme}>
        {/* CssBaseline kickstarts an elegant, consistent baseline to build upon. */}
        <CssBaseline />
        <App />
      </ThemeProvider>
    // </React.StrictMode>,
  );
} else {
  console.error("Failed to find the root element with ID 'root'.");
}
