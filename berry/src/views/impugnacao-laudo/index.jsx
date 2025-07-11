// berry/src/views/impugnacao-laudo/index.jsx
import { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Stack,
  Input,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Fade
} from '@mui/material';
import { UploadFile as UploadFileIcon, Delete as DeleteIcon } from '@mui/icons-material';
import MainCard from 'ui-component/cards/MainCard';
import QuesitosModal from 'ui-component/QuesitosModal';
import { useImpugnacaoLaudoStore } from 'stores/impugnacaoLaudoStore';

// Assuming FRASES_DIVERTIDAS is available or moved to a config file
const FRASES_DIVERTIDAS = [
  'Analisando o juridiquês...',
  'Transformando burocracia em bytes...',
  'Consultando os grandes mestres do Direito...',
  'Aguarde, a petição está quase no ponto...',
  'Desvendando os segredos do laudo pericial...'
];

const ImpugnacaoLaudoPage = () => {
  // Local state
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uiMessage, setUiMessage] = useState(null);
  const [fraseDivertida, setFraseDivertida] = useState('');
  const fileInputRef = useRef(null);
  const intervalRef = useRef(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Global state from the store
  const { isLoading, error, impugnacaoResult, gerarImpugnacao, currentFileBeingProcessed, clearState } = useImpugnacaoLaudoStore();

  // Effect to open modal when results are ready
  useEffect(() => {
    if (impugnacaoResult && !isLoading) {
      setIsModalOpen(true);
    }
  }, [impugnacaoResult, isLoading]);

  // Effect to clear state on component unmount
  useEffect(() => {
    return () => {
      clearState();
    };
  }, [clearState]);

  // Effect for funny phrases
  useEffect(() => {
    if (isLoading) {
      setFraseDivertida(FRASES_DIVERTIDAS[Math.floor(Math.random() * FRASES_DIVERTIDAS.length)]);
      intervalRef.current = setInterval(() => {
        setFraseDivertida((currentPhrase) => {
          let newPhrase;
          do {
            newPhrase = FRASES_DIVERTIDAS[Math.floor(Math.random() * FRASES_DIVERTIDAS.length)];
          } while (newPhrase === currentPhrase && FRASES_DIVERTIDAS.length > 1);
          return newPhrase;
        });
      }, 4000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setFraseDivertida('');
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isLoading]);

  // Handlers
  const handleFileChange = (event) => {
    const files = event.target.files;
    let newFilesToAdd = [];
    let skippedCount = 0;
    let nonPdfCount = 0;
    setUiMessage(null);
    if (files) {
      const potentialFiles = Array.from(files);
      potentialFiles.forEach((file) => {
        if (file.type !== 'application/pdf') {
          nonPdfCount++;
          return;
        }
        const isDuplicate = selectedFiles.some((existingFile) => existingFile.name === file.name && existingFile.size === file.size);
        if (isDuplicate) {
          skippedCount++;
        } else {
          newFilesToAdd.push(file);
        }
      });
      if (newFilesToAdd.length > 0) {
        setSelectedFiles((prevFiles) => [...prevFiles, ...newFilesToAdd]);
      }
      let message = '';
      if (nonPdfCount > 0) {
        message += `${nonPdfCount} arquivo(s) ignorado(s) por não ser(em) PDF. `;
      }
      if (skippedCount > 0) {
        message += `${skippedCount} arquivo(s) duplicado(s) ignorado(s).`;
      }
      setUiMessage(message.trim() || null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = (indexToRemove) => {
    setSelectedFiles((prevFiles) => prevFiles.filter((_, index) => index !== indexToRemove));
  };

  const handleGerarImpugnacao = () => {
    setUiMessage(null);
    if (selectedFiles.length === 0) {
      setUiMessage('Nenhum arquivo PDF selecionado.');
      return;
    }
    const fileToProcess = selectedFiles[0];
    gerarImpugnacao(fileToProcess);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    clearState(); // Clear the result when modal is closed
  };

  return (
    <MainCard title="Impugnação de Laudo Pericial">
      <Stack spacing={3}>
        <Typography variant="body1" gutterBottom align="center">
          Envie o laudo pericial e demais documentos pertinentes para gerar a impugnação.
        </Typography>

        {!isLoading && (
          <Box sx={{ textAlign: 'center', p: 2, border: '2px dashed', borderColor: 'grey.400', borderRadius: 2, bgcolor: 'grey.50' }}>
            <Button variant="contained" onClick={handleUploadClick} startIcon={<UploadFileIcon />} disabled={isLoading} size="large">
              Adicionar PDF(s)
            </Button>
            <Input
              type="file"
              inputRef={fileInputRef}
              onChange={handleFileChange}
              inputProps={{ accept: '.pdf', multiple: true }}
              sx={{ display: 'none' }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Arraste e solte ou clique para selecionar.
            </Typography>
          </Box>
        )}

        {isLoading && (
          <Paper elevation={0} sx={{ p: 2, textAlign: 'center', bgcolor: 'action.hover' }}>
            <Typography variant="h6" component="p" gutterBottom>
              {currentFileBeingProcessed ? `Processando: ${currentFileBeingProcessed.name}` : 'Aguardando...'}
            </Typography>
            <Fade in={!!fraseDivertida} timeout={300}>
              <Typography variant="body1" align="center" sx={{ mt: 1, fontStyle: 'italic', display: 'block', minHeight: '1.5em' }}>
                {fraseDivertida || ' '}
              </Typography>
            </Fade>
          </Paper>
        )}

        {selectedFiles.length > 0 && (
          <Paper variant="outlined" sx={{ p: 2, mt: 2, maxHeight: '250px', overflowY: 'auto', borderRadius: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Arquivos Selecionados:
            </Typography>
            <List dense>
              {selectedFiles.map((file, index) => (
                <ListItem
                  key={`${file.name}-${index}`}
                  secondaryAction={
                    <IconButton edge="end" aria-label="delete" onClick={() => handleRemoveFile(index)} disabled={isLoading}>
                      <DeleteIcon />
                    </IconButton>
                  }
                >
                  <ListItemText primary={file.name} secondary={`${(file.size / 1024).toFixed(1)} KB`} />
                </ListItem>
              ))}
            </List>
          </Paper>
        )}

        {uiMessage && !isLoading && (
          <Alert severity={uiMessage.includes('duplicado') || uiMessage.includes('ignorados') ? 'info' : 'warning'} sx={{ mt: 2 }}>
            {uiMessage}
          </Alert>
        )}

        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleGerarImpugnacao}
            disabled={isLoading || selectedFiles.length === 0}
            sx={{ minWidth: '200px', py: 1.5 }}
          >
            {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Gerar Impugnação'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        <QuesitosModal open={isModalOpen} onClose={handleCloseModal} title="Impugnação Gerada" content={impugnacaoResult || ''} />
      </Stack>
    </MainCard>
  );
};

export default ImpugnacaoLaudoPage;