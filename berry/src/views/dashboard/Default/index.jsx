import { Link } from 'react-router-dom';
import { Grid, Card, CardContent, Typography, Box } from '@mui/material';
import { styled, useTheme } from '@mui/material/styles';

// project imports
import MainCard from 'ui-component/cards/MainCard';
import { gridSpacing } from 'store/constant';

// assets
import { IconHelp, IconSitemap, IconFileText, IconZoomCheck } from '@tabler/icons-react';

// ==============================|| MODULE CARD STYLING ||============================== //

const CardWrapper = styled(MainCard)(({ theme }) => ({
  backgroundColor: theme.palette.secondary.dark,
  color: '#fff',
  overflow: 'hidden',
  position: 'relative',
  transition: 'transform 0.3s ease-in-out',
  '&:hover': {
    transform: 'scale(1.05)',
    boxShadow: theme.shadows[10]
  },
  '&:before': {
    content: '""',
    position: 'absolute',
    width: 210,
    height: 210,
    background: theme.palette.secondary[800],
    borderRadius: '50%',
    top: -125,
    right: -15,
    opacity: 0.5,
    [theme.breakpoints.down('sm')]: {
      top: -155,
      right: -70
    }
  }
}));

// ==============================|| MODULE CARD COMPONENT ||============================== //

const ModuleCard = ({ to, icon, title, description }) => {
  const theme = useTheme();
  const IconComponent = icon;

  return (
    <Grid item lg={6} md={6} sm={12} xs={12}>
      <Link to={to} style={{ textDecoration: 'none' }}>
        <CardWrapper border={false} content={false}>
          <Box sx={{ p: 2.25 }}>
            <Grid container direction="column">
              <Grid item>
                <Grid container justifyContent="space-between">
                  <Grid item>
                    <IconComponent size="2.5rem" color={theme.palette.secondary[200]} />
                  </Grid>
                </Grid>
              </Grid>
              <Grid item sx={{ mt: 1.5 }}>
                <Typography variant="h3" sx={{ color: '#fff' }}>
                  {title}
                </Typography>
              </Grid>
              <Grid item>
                <Typography sx={{ mt: 1, fontSize: '0.875rem', fontWeight: 500, color: theme.palette.secondary[200] }}>
                  {description}
                </Typography>
              </Grid>
            </Grid>
          </Box>
        </CardWrapper>
      </Link>
    </Grid>
  );
};

// ==============================|| DEFAULT DASHBOARD ||============================== //

const Dashboard = () => {
  const modules = [
    {
      to: '/gerador-quesitos',
      icon: IconHelp,
      title: 'Gerador de Quesitos',
      description: 'Crie quesitos personalizados a partir de documentos PDF.'
    },
    {
      to: '/impugnacao-laudo',
      icon: IconSitemap,
      title: 'Impugnação de Laudo',
      description: 'Gere uma impugnação de laudo pericial de forma rápida.'
    },
    {
      to: '/recurso-judicial',
      icon: IconFileText,
      title: 'Recurso Judicial',
      description: 'Elabore um recurso judicial a partir da sentença e outros documentos.'
    },
    {
      to: '/analise-docs-medicos',
      icon: IconZoomCheck,
      title: 'Análise de Documentos',
      description: 'Analise documentos médicos para extrair informações relevantes.'
    }
  ];

  return (
    <Grid container spacing={gridSpacing}>
      <Grid item xs={12}>
        <Typography variant="h2" gutterBottom>
          Módulos Disponíveis
        </Typography>
        <Typography variant="subtitle1">
          Selecione uma das ferramentas abaixo para começar.
        </Typography>
      </Grid>
      <Grid item xs={12}>
        <Grid container spacing={gridSpacing}>
          {modules.map((module, index) => (
            <ModuleCard
              key={index}
              to={module.to}
              icon={module.icon}
              title={module.title}
              description={module.description}
            />
          ))}
        </Grid>
      </Grid>
    </Grid>
  );
};

export default Dashboard;