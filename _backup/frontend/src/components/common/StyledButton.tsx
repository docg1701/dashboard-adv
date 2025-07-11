import React from 'react';
import Button, { ButtonProps } from '@mui/material/Button';

// Define any project-specific default props or styles if needed
// For now, it can be a simple re-export or a light wrapper

const StyledButton: React.FC<ButtonProps> = (props) => {
  // Example: Enforce a default variant if not provided, or apply sx prop
  // const { variant = 'contained', children, ...rest } = props;
  return (
    <Button {...props}>
      {props.children}
    </Button>
  );
};

export default StyledButton;
