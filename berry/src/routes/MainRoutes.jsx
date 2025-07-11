import { lazy } from 'react';

// project imports
import MainLayout from 'layout/MainLayout';
import Loadable from 'ui-component/Loadable';
import ProtectedRoute from './ProtectedRoute';

// dashboard routing
const DashboardDefault = Loadable(lazy(() => import('views/dashboard/Default')));

// module pages
const GeradorQuesitosPage = Loadable(lazy(() => import('views/gerador-quesitos')));
const ImpugnacaoLaudoPage = Loadable(lazy(() => import('views/impugnacao-laudo')));
const RecursoJudicialPage = Loadable(lazy(() => import('views/recurso-judicial')));
const AnaliseDocsMedicosPage = Loadable(lazy(() => import('views/analise-docs-medicos')));

// ==============================|| MAIN ROUTING ||============================== //

const MainRoutes = {
  path: '/',
  element: (
    <ProtectedRoute>
      <MainLayout />
    </ProtectedRoute>
  ),
  children: [
    {
      path: '/',
      element: <DashboardDefault />
    },
    {
      path: 'dashboard',
      children: [
        {
          path: 'default',
          element: <DashboardDefault />
        }
      ]
    },
    {
      path: 'gerador-quesitos',
      element: <GeradorQuesitosPage />
    },
    {
      path: 'impugnacao-laudo',
      element: <ImpugnacaoLaudoPage />
    },
    {
      path: 'recurso-judicial',
      element: <RecursoJudicialPage />
    },
    {
      path: 'analise-docs-medicos',
      element: <AnaliseDocsMedicosPage />
    }
  ]
};

export default MainRoutes;
