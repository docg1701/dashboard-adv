import React, { ReactNode } from 'react';
import Card, { CardProps } from '@mui/material/Card';
import CardHeader, { CardHeaderProps } from '@mui/material/CardHeader';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions'; // Optional

interface InfoCardProps extends Omit<CardProps, 'title'> {
  title?: ReactNode; // Allow title to be passed directly or via CardHeaderProps
  subheader?: ReactNode;
  headerProps?: Partial<CardHeaderProps>;
  action?: ReactNode; // For CardHeader action
  children: ReactNode; // Content of the card
  cardActions?: ReactNode; // Optional actions at the bottom
}

const InfoCard: React.FC<InfoCardProps> = ({
  title,
  subheader,
  headerProps,
  action,
  children,
  cardActions,
  ...rest
}) => {
  return (
    <Card {...rest}>
      {(title || action) && (
        <CardHeader title={title} subheader={subheader} action={action} {...headerProps} />
      )}
      <CardContent>
        {children}
      </CardContent>
      {cardActions && <CardActions>{cardActions}</CardActions>}
    </Card>
  );
};

export default InfoCard;
