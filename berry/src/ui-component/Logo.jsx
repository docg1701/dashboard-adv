import defaultLogo from 'assets/images/iamlogo.png';

export default function Logo({ logo = defaultLogo, width = '100' }) {
  return <img src={logo} alt="IA.M" width={width} />;
}

