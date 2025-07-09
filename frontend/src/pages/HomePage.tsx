import React from 'react';
import { Container, Typography, Grid, Card, CardActionArea, CardContent, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getModuleRegistry, ModuleConfig } from '../config/moduleRegistry';
import { useAuthStore } from '../stores/authStore'; // Using useAuthStore based on MainLayout
import { SvgIconComponent } from '@mui/icons-material';

const HomePage: React.FC = () => {
  const { user } = useAuthStore(); // Using useAuthStore
  const moduleRegistry = getModuleRegistry();

  // Determine user role for filtering. Adapt if user.role is an array e.g. user.roles.includes('ADMIN')
  const isAdmin = user?.role === 'ADMIN';

  const availableModules = Object.values(moduleRegistry).filter(
    (module) => !module.adminOnly || (module.adminOnly && isAdmin)
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      

      {availableModules.length > 0 ? (
        <Grid container spacing={3}>
          {availableModules.map((module: ModuleConfig) => {
            const IconComponent = module.navIcon as SvgIconComponent | undefined;
            return (
              <Grid item xs={12} sm={6} md={4} key={module.name}>
                <Card sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <CardActionArea component={RouterLink} to={module.basePath} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', p: 2, flexGrow: 1 }}>
                      {IconComponent && (
                        <IconComponent sx={{ fontSize: 40, mr: 2 }} />
                      )}
                      <CardContent sx={{ flexGrow: 1, p:0, '&:last-child': { pb: 0 } }}>
                        <Typography gutterBottom variant="h5" component="div">
                          {module.navText}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {module.name}
                          {module.adminOnly && <Typography variant="caption" display="block" sx={{color: 'warning.main'}}> (Admin Only)</Typography>}
                        </Typography>
                      </CardContent>
                    </Box>
                  </CardActionArea>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      ) : (
        <Typography variant="body1">
          No modules are currently available to you.
        </Typography>
      )}
    </Container>
  );
};

export default HomePage;