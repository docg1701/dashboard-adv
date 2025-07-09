// frontend/src/modules/impugnacao_laudo/ImpugnacaoLaudo.tsx
import React, { useState, useRef, ChangeEvent, useEffect } from 'react';
import {
    Box, Button, Typography, CircularProgress, Alert, Paper, Stack,
    Input, List, ListItem, ListItemText, IconButton, Fade
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DeleteIcon from '@mui/icons-material/Delete';
import { FRASES_DIVERTIDAS } from '../../config/opcoesFormulario';
import { useImpugnacaoLaudoStore } from './impugnacaoLaudoStore';
import QuesitosModal from '../../components/common/QuesitosModal';

const ImpugnacaoLaudo: React.FC = () => {
    // Local state
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [uiMessage, setUiMessage] = useState<string | null>(null);
    const [fraseDivertida, setFraseDivertida] = useState<string>('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Global state from the store
    const {
        isLoading,
        error,
        impugnacaoResult,
        gerarImpugnacao,
        currentFileBeingProcessed,
    } = useImpugnacaoLaudoStore();

    // Effect to open modal when results are ready
    useEffect(() => {
        if (impugnacaoResult && !isLoading) {
            setIsModalOpen(true);
        }
    }, [impugnacaoResult, isLoading]);

    // Effect for funny phrases
    useEffect(() => {
        if (isLoading) {
            setFraseDivertida(FRASES_DIVERTIDAS[Math.floor(Math.random() * FRASES_DIVERTIDAS.length)]);
            intervalRef.current = setInterval(() => {
                setFraseDivertida(currentPhrase => {
                    let newPhrase;
                    do {
                        newPhrase = FRASES_DIVERTIDAS[Math.floor(Math.random() * FRASES_DIVERTIDAS.length)];
                    } while (newPhrase === currentPhrase && FRASES_DIVERTIDAS.length > 1);
                    return newPhrase;
                });
            }, 4000);
        } else {
            if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
            setFraseDivertida('');
        }
        return () => { if (intervalRef.current) { clearInterval(intervalRef.current); } };
    }, [isLoading]);

    // Handlers
    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        let newFilesToAdd: File[] = [];
        let skippedCount = 0;
        let nonPdfCount = 0;
        setUiMessage(null);
        if (files) {
            const potentialFiles = Array.from(files);
            potentialFiles.forEach(file => {
                if (file.type !== 'application/pdf') { nonPdfCount++; return; }
                const isDuplicate = selectedFiles.some(
                    existingFile => existingFile.name === file.name && existingFile.size === file.size
                );
                if (isDuplicate) { skippedCount++; } else { newFilesToAdd.push(file); }
            });
            if (newFilesToAdd.length > 0) { setSelectedFiles(prevFiles => [...prevFiles, ...newFilesToAdd]); }
            let message = '';
            if (nonPdfCount > 0) { message += `${nonPdfCount} arquivo(s) ignorado(s) por não ser(em) PDF. `; }
            if (skippedCount > 0) { message += `${skippedCount} arquivo(s) duplicado(s) ignorado(s).`; }
            setUiMessage(message.trim() || null);
        }
        if (fileInputRef.current) { fileInputRef.current.value = ''; }
    };
    const handleUploadClick = () => { fileInputRef.current?.click(); };
    const handleRemoveFile = (indexToRemove: number) => { setSelectedFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToRemove)); };

    const handleGerarImpugnacao = () => {
        setUiMessage(null);
        if (selectedFiles.length === 0) {
            setUiMessage("Nenhum arquivo PDF selecionado.");
            return;
        }
        const fileToProcess = selectedFiles[0];
        gerarImpugnacao(fileToProcess);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
    };

    return (
        <Stack spacing={3}>
            {!isLoading ? ( /* Inputs */ <>
               <Box>
                   <Button variant="outlined" onClick={handleUploadClick} startIcon={<UploadFileIcon />} disabled={isLoading}> Adicionar PDF(s) </Button>
                   <Input type="file" inputRef={fileInputRef} onChange={handleFileChange} inputProps={{ accept: '.pdf', multiple: true, 'data-testid': 'file-input-impugnacao-laudo' }} sx={{ display: 'none' }} />
               </Box>
            </> ) : ( /* Loading State Display */
                <Paper elevation={0} sx={{ p: 2, textAlign: 'center', bgcolor: 'action.hover' }}>
                    <Typography variant="h5" component="p" gutterBottom>
                        {currentFileBeingProcessed ? `Processando: ${currentFileBeingProcessed.name}` : "Aguardando Ação..."}
                    </Typography>
                </Paper>
            )}
            {selectedFiles.length > 0 && ( /* File List */ <Paper variant="outlined" sx={{ p: 1, mt: 1, maxHeight: '200px', overflowY: 'auto' }}>
                 <Typography variant="subtitle2" gutterBottom sx={{ pl: 1 }}>
                     {selectedFiles.length > 1 ? `Arquivo para processar: ${selectedFiles[0].name} (de ${selectedFiles.length} selecionados)` : `Arquivo Selecionado: ${selectedFiles[0].name}`}
                 </Typography>
                <List dense>
                    {selectedFiles.map((file, index) => (
                        <ListItem key={`${file.name}-${index}-${file.lastModified}`} secondaryAction={ <IconButton edge="end" aria-label="delete" onClick={() => handleRemoveFile(index)} disabled={isLoading}> <DeleteIcon fontSize="small"/> </IconButton> } sx={{py: 0}}>
                            <ListItemText primary={file.name} secondary={`${(file.size / 1024).toFixed(1)} KB`} primaryTypographyProps={{ sx: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }} />
                        </ListItem>
                    ))}
                </List>
            </Paper> )}
             {uiMessage && !isLoading && ( <Alert severity={uiMessage.includes('duplicado') || uiMessage.includes('ignorados') ? 'info' : 'warning'} sx={{ mt: 1 }}> {uiMessage} </Alert> )}
            <Box sx={{ textAlign: 'center', mt: 2 }}> {/* Submit Button */}
                <Button variant="contained" color="primary" onClick={handleGerarImpugnacao} disabled={isLoading || selectedFiles.length === 0} sx={{ minWidth: '180px', px: 3, py: 1.5, fontSize: '1rem' }}>
                    {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Gerar Impugnação'}
                </Button>
            </Box>
            {/* Display Funny Phrase during loading */}
            {isLoading && (
                 <Fade in={!!fraseDivertida} timeout={300}>
                     <Box>
                         <Typography variant="body1" align="center" sx={{ mt: 1, fontStyle: 'italic', display: 'block', minHeight: '1.5em' }}>
                             {fraseDivertida || '\u00A0'}
                         </Typography>
                     </Box>
                </Fade>
            )}
            {error && ( /* API Error */ <Alert severity="error" sx={{ mt: 2 }}> {error} </Alert> )}
            
            {/* Render the modal */}
            <QuesitosModal
                open={isModalOpen}
                onClose={handleCloseModal}
                title="Impugnação Gerada"
                content={impugnacaoResult || ''}
            />
        </Stack>
    );
};

export default ImpugnacaoLaudo;
