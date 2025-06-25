import React, { ComponentType, LazyExoticComponent } from 'react';
import { SvgIconComponent } from '@mui/icons-material';
import BuildIcon from '@mui/icons-material/Build'; // Example Icon
import GavelIcon from '@mui/icons-material/Gavel'; // Icon for Gerador Quesitos
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'; // Icon for System Info
import DescriptionIcon from '@mui/icons-material/Description'; // Icon for PDF Transcriber

export interface ModuleRoute {
  path: string;
  component: LazyExoticComponent<ComponentType<any>>;
  exact?: boolean;
}

export interface ModuleConfig {
  name: string;
  basePath: string; // e.g., /gerador-quesitos
  routes: ModuleRoute[]; // Routes specific to the module
  navIcon?: SvgIconComponent | string; // MUI Icon or path to an image
  navText?: string; // Text for navigation, defaults to 'name'
  adminOnly?: boolean; // If the module should only be accessible by admin users
  // Add other module-specific properties here as needed
}

export interface ModuleRegistry {
  [key: string]: ModuleConfig;
}

// Example Usage (will be populated by actual modules later)
const moduleRegistry: ModuleRegistry = {
  // ... (any existing modules) ...
  testModule: {
    name: 'Test Module',
    basePath: '/test-module',
    navIcon: BuildIcon,
    navText: 'Test Module',
    adminOnly: false,
    routes: [
      {
        path: '/', // Root path for this module
        component: React.lazy(() => import('../modules/test_module/TestModulePage')),
        exact: true,
      },
    ],
  },
  geradorQuesitos: {
    name: 'Gerador de Quesitos',
    basePath: '/gerador-quesitos',
    navIcon: GavelIcon,
    navText: 'Gerador Quesitos',
    adminOnly: false, // Assuming it's not admin only, adjust if needed
    routes: [
      {
        path: '/',
        component: React.lazy(() => import('../pages/PaginaGeradorQuesitos')),
        exact: true,
      },
    ],
  },
  systemInfo: {
    name: 'System Info',
    basePath: '/system-info',
    navIcon: InfoOutlinedIcon,
    navText: 'System Info',
    adminOnly: false, // Assuming it's not admin only, adjust if needed
    routes: [
      {
        path: '/',
        component: React.lazy(() => import('../pages/SystemInfoPage')),
        exact: true,
      },
    ],
  },
  transcritorPdfTester: { // Changed key
    name: 'Transcritor PDF Tester', // Changed display name
    basePath: '/transcritor-pdf-tester', // Optional: change base path for consistency
    navIcon: DescriptionIcon,
    navText: 'Transcritor PDF Tester', // Changed nav text
    adminOnly: false,
    routes: [
      {
        path: '/',
        component: React.lazy(() => import('../modules/transcritor_pdf_tester/TranscritorPdfTesterPage')), // Updated import path
        exact: true,
      },
    ],
  },
};

export const getModuleRegistry = (): ModuleRegistry => {
  // In the future, this could load modules dynamically,
  // e.g., from a configuration file or based on user roles.
  return moduleRegistry;
};

export const registerModule = (moduleId: string, config: ModuleConfig): void => {
  if (moduleRegistry[moduleId]) {
    console.warn(`Module with id "${moduleId}" is already registered. Overwriting.`);
  }
  moduleRegistry[moduleId] = config;
  console.log(`Module "${moduleId}" registered.`);
};

export const getModule = (moduleId: string): ModuleConfig | undefined => {
  return moduleRegistry[moduleId];
};

export default moduleRegistry;
