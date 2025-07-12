// assets
import { IconHelp, IconSitemap, IconFileText, IconZoomCheck } from '@tabler/icons-react';

// constant
const icons = { IconHelp, IconSitemap, IconFileText, IconZoomCheck };

// ==============================|| MODULES MENU ITEMS ||============================== //

const modules = {
  id: 'modules',
  title: 'Módulos',
  type: 'group',
  children: [
    {
      id: 'gerador-quesitos',
      title: 'Quesitos',
      type: 'item',
      url: '/gerador-quesitos',
      icon: icons.IconHelp,
      breadcrumbs: false
    },
    {
      id: 'impugnacao-laudo',
      title: 'Impugnação de Laudo',
      type: 'item',
      url: '/impugnacao-laudo',
      icon: icons.IconSitemap,
      breadcrumbs: false
    },
    {
      id: 'recurso-judicial',
      title: 'Recurso Judicial',
      type: 'item',
      url: '/recurso-judicial',
      icon: icons.IconFileText,
      breadcrumbs: false
    },
    {
      id: 'analise-docs-medicos',
      title: 'Análise Docs',
      type: 'item',
      url: '/analise-docs-medicos',
      icon: icons.IconZoomCheck,
      breadcrumbs: false
    }
  ]
};

export default modules;
