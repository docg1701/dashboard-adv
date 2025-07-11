import React, { ReactNode } from 'react';
import Dialog, { DialogProps } from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close'; // For a close button

interface StandardModalProps extends Omit<DialogProps, 'title'> {
  title: ReactNode;
  children: ReactNode; // Content for DialogContent
  actions?: ReactNode; // Content for DialogActions
  showCloseButton?: boolean;
  onClose?: () => void; // Ensure onClose is part of props if showCloseButton is true
}

const StandardModal: React.FC<StandardModalProps> = ({
  title,
  children,
  actions,
  open,
  showCloseButton = true, // Default to showing close button
  onClose,
  ...rest
}) => {
  return (
    <Dialog open={open} onClose={onClose} {...rest}>
      <DialogTitle sx={{ m: 0, p: 2 }}>
        {title}
        {showCloseButton && onClose ? (
          <IconButton
            aria-label="close"
            onClick={onClose}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: (theme) => theme.palette.grey[500],
            }}
          >
            <CloseIcon />
          </IconButton>
        ) : null}
      </DialogTitle>
      <DialogContent dividers> {/* Dividers add top/bottom borders */}
        {children}
      </DialogContent>
      {actions && <DialogActions>{actions}</DialogActions>}
    </Dialog>
  );
};

export default StandardModal;
