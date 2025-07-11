// frontend/src/utils/iconMap.tsx
import React from 'react';

// Import specific MUI icons defined in navigation.ts
// Add more imports here as new icons are needed for future modules
import HomeIcon from '@mui/icons-material/Home';
import InfoIcon from '@mui/icons-material/Info';
import ArticleIcon from '@mui/icons-material/Article';
// import MemoryIcon from '@mui/icons-material/Memory'; // Example for future
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'; // Default fallback icon

// Define the mapping from string identifier to icon component
// Use React.ElementType to type the icon components
// Ensure keys match the 'icon' string values used in navigation.ts
const iconMap: { [key: string]: React.ElementType } = {
  Home: HomeIcon,
  Info: InfoIcon,
  Article: ArticleIcon,
  // Memory: MemoryIcon, // Example
  // Add other mappings here
};

/**
 * Gets the corresponding MUI Icon component for a given string identifier.
 * Returns a default icon if the identifier is not found.
 * @param iconName The string identifier (e.g., 'Home', 'Info') from navigation config.
 * @returns The MUI Icon component or a default fallback icon.
 */
export const getIconComponent = (iconName: string): React.ElementType => {
  const IconComponent = iconMap[iconName];
  if (IconComponent) {
    return IconComponent;
  } else {
    console.warn(`Icon mapping not found for "${iconName}". Using default.`);
    return HelpOutlineIcon; // Return fallback icon if name not found
  }
};