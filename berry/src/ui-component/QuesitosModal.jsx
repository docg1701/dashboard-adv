import { useState } from 'react';
import {
    Modal, Box, Typography, IconButton, Button, Tooltip, Fade
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

const modalStyle = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '80%',
    maxWidth: '800px',
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
    display: 'flex',
    flexDirection: 'column',
    maxHeight: '90vh',
};

const contentStyle = {
    mt: 2,
    whiteSpace: 'pre-wrap',
    overflowY: 'auto',
    flexGrow: 1,
    p: 2,
    bgcolor: 'grey.100',
    border: '1px solid #ddd',
    borderRadius: '4px',
};

const QuesitosModal = ({ open, onClose, title, content }) => {
    const [copyTooltipText, setCopyTooltipText] = useState('Copiar para Área de Transferência');

    const handleCopy = () => {
        navigator.clipboard.writeText(content).then(() => {
            setCopyTooltipText('Copiado!');
            setTimeout(() => setCopyTooltipText('Copiar para Área de Transferência'), 2000);
        }, (err) => {
            setCopyTooltipText('Falha ao copiar!');
            console.error('Could not copy text: ', err);
        });
    };

    return (
        <Modal
            open={open}
            onClose={onClose}
            aria-labelledby="quesitos-modal-title"
            aria-describedby="quesitos-modal-content"
            closeAfterTransition
        >
            <Fade in={open}>
                <Box sx={modalStyle}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                        <Typography id="quesitos-modal-title" variant="h6" component="h2">
                            {title}
                        </Typography>
                        <Tooltip title={copyTooltipText} placement="bottom">
                            <Button
                                variant="outlined"
                                startIcon={<ContentCopyIcon />}
                                onClick={handleCopy}
                                sx={{ mr: 1 }}
                            >
                                Copiar
                            </Button>
                        </Tooltip>
                        <IconButton
                            aria-label="close"
                            onClick={onClose}
                            sx={{
                                color: (theme) => theme.palette.grey[500],
                            }}
                        >
                            <CloseIcon />
                        </IconButton>
                    </Box>
                    <Box id="quesitos-modal-content" sx={contentStyle}>
                        <Typography variant="body2">{content}</Typography>
                    </Box>
                </Box>
            </Fade>
        </Modal>
    );
};

export default QuesitosModal;
