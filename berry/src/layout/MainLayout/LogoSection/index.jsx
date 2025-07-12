import { Link as RouterLink } from 'react-router-dom';

// material-ui
import Link from '@mui/material/Link';

// project imports
import Logo from 'ui-component/Logo';
import horizontalLogo from 'assets/images/iamlogohorizontal.png';

// ==============================|| MAIN LOGO ||============================== //

export default function LogoSection() {
  return (
    <Link component={RouterLink} to="/" aria-label="theme-logo">
      <Logo logo={horizontalLogo} width="100" />
    </Link>
  );
}
