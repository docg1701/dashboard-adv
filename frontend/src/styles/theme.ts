// frontend/src/styles/theme.ts
import { createTheme } from '@mui/material/styles';
import { red } from '@mui/material/colors';

// Create a theme instance.
const theme = createTheme({
  palette: {
    mode: 'light', // Default to light mode, can be 'dark'
    primary: {
      main: '#4257b2', // Darker shade of blue
    },
    secondary: {
      main: '#19857b', // Example secondary color
    },
    error: {
      main: red.A400, // Use red from MUI colors for errors
    },
    // background: { // Optional: customize background colors
    //   default: '#fff',
    // },
  },
  typography: { // Optional: customize typography
    fontFamily: [
      'Public Sans',
      'sans-serif',
    ].join(','),
    // You can define variants like h1, h2, body1, etc.
    // h1: {
    //   fontSize: '2.5rem',
    // },
  },
  components: { // Optional: Override default component styles
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#000', // Set AppBar background to black
          color: '#fff', // Set AppBar text color to white
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // Example: disable uppercase buttons
        },
      },
    },
  },
});

export default theme;