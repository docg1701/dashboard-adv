import React from 'react';
import { Outlet, Link as RouterLink, useNavigate, NavLink as RouterNavLink, useMatch, useResolvedPath } from 'react-router-dom';
import { styled, useTheme, Theme, alpha } from '@mui/material/styles'; // Added alpha
import useMediaQuery from '@mui/material/useMediaQuery'; // Import useMediaQuery
import {
  AppBar as MuiAppBarCore,
  Toolbar, Typography, Box, Drawer as MuiDrawerCore, List, ListItem, ListItemButton,
  ListItemIcon, ListItemText, IconButton, CssBaseline, Tooltip
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
// import ChevronRightIcon from '@mui/icons-material/ChevronRight'; // Not used in provided example if drawer closes only to left
import HomeIcon from '@mui/icons-material/Home';
import DescriptionIcon from '@mui/icons-material/Description';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import LogoutIcon from '@mui/icons-material/Logout';

import { useAuthStore } from '../stores/authStore';
import { getModuleRegistry, ModuleConfig } from '../config/moduleRegistry';
import { SvgIconComponent } from '@mui/icons-material';

const drawerWidth = 240;

const MuiAppBar = styled(MuiAppBarCore, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }: { theme: Theme, open: boolean }) => ({ // 'open' here refers to the prop passed to MuiAppBar, not the drawer's own state directly if temporary
  zIndex: theme.zIndex.drawer + 1,
  transition: theme.transitions.create(['width', 'margin'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && { // This 'open' means the permanent drawer is open, so shift the AppBar
    marginLeft: drawerWidth,
    width: `calc(100% - ${drawerWidth}px)`,
    transition: theme.transitions.create(['width', 'margin'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const MuiDrawer = styled(MuiDrawerCore, { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme, open, variantProp }: { theme: Theme, open: boolean, variantProp?: string }) => ({ // Added variantProp to pass isSmallScreen
    '& .MuiDrawer-paper': {
      position: 'relative', // Default for permanent
      whiteSpace: 'nowrap',
      width: drawerWidth,
      transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.enteringScreen,
      }),
      boxSizing: 'border-box',
      // Styles for collapsed permanent drawer
      ...(variantProp !== 'temporary' && !open && {
        overflowX: 'hidden',
        transition: theme.transitions.create('width', {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.leavingScreen,
        }),
        width: theme.spacing(7),
        [theme.breakpoints.up('sm')]: {
          width: theme.spacing(9),
        },
      }),
    },
  }),
);


const MainLayout: React.FC = () => {
  const theme = useTheme();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('md'));
  const [open, setOpen] = React.useState(!isSmallScreen); // Closed on small screens, open on large

  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const moduleRegistry = getModuleRegistry();

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Determine user role for filtering. Adapt if user.role is an array e.g. user.roles.includes('ADMIN')
  const isAdmin = user?.role === 'admin'; // Changed to lowercase 'admin'

  // Helper component for NavListItems to handle active state and styling
  interface NavListItemProps {
    to: string;
    primary: string;
    icon: React.ReactElement;
    open: boolean; // Drawer open state
    isSmallScreen: boolean;
    onClick?: () => void;
    exact?: boolean; // For exact path matching
  }

  const NavListItem: React.FC<NavListItemProps> = ({ to, primary, icon, open, isSmallScreen, onClick, exact = false }) => {
    const resolvedPath = useResolvedPath(to);
    const isActive = !!useMatch({ path: resolvedPath.pathname, end: exact });

    return (
      <ListItem disablePadding sx={{ display: 'block' }}>
        <Tooltip title={open ? "" : primary} placement="right">
          <ListItemButton
            component={RouterLink}
            to={to}
            selected={isActive}
            onClick={() => {
              if (isSmallScreen && onClick) {
                onClick();
              }
            }}
            sx={{
              minHeight: 48,
              justifyContent: open ? 'initial' : 'center',
              px: 2.5,
              '&:hover': {
                backgroundColor: theme.palette.action.hover,
              },
              '&.Mui-selected': {
                backgroundColor: alpha(theme.palette.primary.main, 0.08),
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.12),
                },
                '.MuiListItemIcon-root, .MuiListItemText-primary': {
                  color: theme.palette.primary.main,
                },
              },
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 0,
                mr: open ? 3 : 'auto',
                justifyContent: 'center',
              }}
            >
              {icon}
            </ListItemIcon>
            <ListItemText primary={primary} sx={{ opacity: open ? 1 : 0 }} />
          </ListItemButton>
        </Tooltip>
      </ListItem>
    );
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      {/* AppBar's 'open' prop should only be true if the drawer is permanent and open */}
      <MuiAppBar position="absolute" open={open && !isSmallScreen}>
        <Toolbar
          sx={{
            pr: '24px', // keep right padding for actions like logout
          }}
        >
          <IconButton
            edge="start"
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerOpen}
            sx={{
              marginRight: '36px',
              ...(open && !isSmallScreen && { display: 'none' }), // Hide only if permanent drawer is open
              '&:hover': {
                backgroundColor: alpha(theme.palette.common.white, 0.08),
              },
              '&:active': {
                backgroundColor: alpha(theme.palette.common.white, 0.15),
              }
            }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            component="h1"
            variant="h6"
            color="inherit"
            noWrap
            sx={{ flexGrow: 1 }}
          >
            dashboard-adv
          </Typography>
          <Tooltip title="Logout">
            <IconButton color="inherit" onClick={handleLogout}
              sx={{
                '&:hover': {
                  backgroundColor: alpha(theme.palette.common.white, 0.08),
                },
                '&:active': {
                  backgroundColor: alpha(theme.palette.common.white, 0.15),
                }
              }}
            >
              <LogoutIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </MuiAppBar>
      <MuiDrawer variant={isSmallScreen ? "temporary" : "permanent"} open={open} onClose={handleDrawerClose} variantProp={isSmallScreen ? "temporary" : "permanent"}>
        <Toolbar
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            px: [1],
          }}
        >
          <IconButton onClick={handleDrawerClose}
            sx={{
              '&:hover': {
                backgroundColor: alpha(theme.palette.action.hover, 0.08), // Adjusted for potentially lighter background if theme changes
              },
              '&:active': {
                backgroundColor: alpha(theme.palette.action.active, 0.1), // Adjusted
              }
            }}
          >
            <ChevronLeftIcon />
          </IconButton>
        </Toolbar>
        <Box sx={{ overflowY: 'auto', overflowX: 'hidden', height: 'calc(100% - 64px)' }}> {/* Adjust height based on Toolbar */}
          <List component="nav">
            <NavListItem
              to="/"
              primary="Home"
              icon={<HomeIcon />}
              open={open}
              isSmallScreen={isSmallScreen}
              onClick={handleDrawerClose}
              exact={true}
            />
            

            {Object.values(moduleRegistry).filter(module => !module.adminOnly || (module.adminOnly && isAdmin)).map((module: ModuleConfig) => {
              const IconComponent = module.navIcon as SvgIconComponent | undefined;
              return (
                <NavListItem
                  key={module.name}
                  to={module.basePath}
                  primary={module.navText || module.name}
                  icon={IconComponent ? <IconComponent /> : <div style={{ width: 24, height: 24 }} />}
                  open={open}
                  isSmallScreen={isSmallScreen}
                  onClick={handleDrawerClose}
                  exact={module.basePath === '/'} // Assuming only home is truly exact, others might have sub-routes
                />
              );
            })}
          </List>
          {isAdmin && (
            <>
              <Box sx={{ my: 1, mx: open ? 2.5 : 'auto', pl: open ? 0 : 1.5 }}><Typography variant="caption" sx={{ opacity: open ? 0.7 : 0 }}>Admin</Typography></Box>
              <List component="nav">
                <NavListItem
                  to="/admin/users"
                  primary="Admin Users"
                  icon={<AdminPanelSettingsIcon />}
                  open={open}
                  isSmallScreen={isSmallScreen}
                  onClick={handleDrawerClose}
                />
              </List>
            </>
          )}
        </Box>
      </MuiDrawer>
      <Box
        component="main"
        sx={{
          backgroundColor: (theme) => // theme is accessible here
            theme.palette.mode === 'light'
              ? theme.palette.grey[100]
              : theme.palette.grey[900],
          flexGrow: 1,
          height: '100vh',
          overflow: 'auto',
        }}
      >
        <Toolbar />
        {/* Responsive padding for the main content area */}
        <Box sx={{ p: { xs: 1, sm: 2, md: 3 } }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default MainLayout;