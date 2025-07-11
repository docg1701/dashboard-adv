// frontend/src/modules/analise_docs_medicos/AnaliseDocsMedicos.tsx
import React, { useState, useRef, ChangeEvent, useEffect } from 'react';
import {
    Box, Button, Typography, CircularProgress, Alert, Paper, Stack, Container,
    Input, List, ListItem, ListItemText, IconButton, Fade
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DeleteIcon from '@mui/icons-material/Delete';
import { FRASES_DIVERTIDAS } from '../../config/opcoesFormulario';
import { useAnaliseDocsMedicosStore } from './analiseDocsMedicosStore';
import QuesitosModal from '../../components/common/QuesitosModal';

const AnaliseDocsMedicos: React.FC = () => {
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
        analiseResult,
        gerarAnalise,
        currentFileBeingProcessed,
        clearState,
    } = useAnaliseDocsMedicosStore();

    // Effect to open modal when results are ready
    useEffect(() => {
        if (analiseResult && !isLoading) {
            setIsModalOpen(true);
        }
    }, [analiseResult, isLoading]);

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

    const handleGerarAnalise = () => {
        setUiMessage(null);
        if (selectedFiles.length === 0) {
            setUiMessage("Nenhum arquivo PDF selecionado.");
            return;
        }
        const fileToProcess = selectedFiles[0];
        gerarAnalise(fileToProcess);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        clearState();
    };

    return (
        <Container maxWidth="md" sx={{ mt: 4, mb: 4, p: 4, borderRadius: '12px', overflow: 'hidden' }}>
            <Stack spacing={3}>
                    <Typography variant="h5" component="h2" gutterBottom align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>
                        Envie a documentação médica para análise
                    </Typography>

                    {!isLoading ? ( /* Inputs */
                        <Box sx={{ textAlign: 'center', p: 2, border: '2px dashed', borderColor: 'grey.400', borderRadius: '8px', bgcolor: 'grey.50' }}>
                            <Button variant="contained" onClick={handleUploadClick} startIcon={<UploadFileIcon />} disabled={isLoading} size="large">
                                Adicionar PDF(s)
                            </Button>
                            <Input type="file" inputRef={fileInputRef} onChange={handleFileChange} inputProps={{ accept: '.pdf', multiple: true, 'data-testid': 'file-input-analise-docs' }} sx={{ display: 'none' }} />
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                Arraste e solte seus arquivos PDF aqui, ou clique para selecionar.
                            </Typography>
                        </Box>
                    ) : ( /* Loading State Display */
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', bgcolor: 'action.hover' }}>
                            <Typography variant="h5" component="p" gutterBottom>
                                {currentFileBeingProcessed ? `Processando: ${currentFileBeingProcessed.name}` : "Aguardando Ação..."}
                            </Typography>
                            
                        </Paper>
                    )}

                    {selectedFiles.length > 0 && ( /* File List */
                        <Paper variant="outlined" sx={{ p: 2, mt: 2, maxHeight: '250px', overflowY: 'auto', borderRadius: '8px', borderColor: 'grey.300' }}>
                            <Typography variant="subtitle1" gutterBottom sx={{ mb: 1, fontWeight: 500 }}>
                                Arquivos Selecionados:
                            </Typography>
                            <List dense>
                                {selectedFiles.map((file, index) => (
                                    <ListItem
                                        key={`${file.name}-${index}-${file.lastModified}`}
                                        secondaryAction={
                                            <IconButton edge="end" aria-label="delete" onClick={() => handleRemoveFile(index)} disabled={isLoading} size="small">
                                                <DeleteIcon fontSize="small" />
                                            </IconButton>
                                        }
                                        sx={{ py: 0.5 }}
                                    >
                                        <ListItemText
                                            primary={file.name}
                                            secondary={`${(file.size / 1024).toFixed(1)} KB`}
                                            primaryTypographyProps={{ sx: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </Paper>
                    )}

                    {uiMessage && !isLoading && (
                        <Alert severity={uiMessage.includes('duplicado') || uiMessage.includes('ignorados') ? 'info' : 'warning'} sx={{ mt: 2, borderRadius: '8px' }}>
                            {uiMessage}
                        </Alert>
                    )}

                    <Box sx={{ textAlign: 'center', mt: 2 }}> {/* Submit Button */}
                        <Button variant="contained" color="primary" onClick={handleGerarAnalise} disabled={isLoading || selectedFiles.length === 0} sx={{ minWidth: '180px', px: 3, py: 1.5, fontSize: '1rem' }}>
                            {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Gerar Análise'}
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

                    {error && ( /* API Error */
                        <Alert severity="error" sx={{ mt: 2, borderRadius: '8px' }}>
                            {error}
                        </Alert>
                    )}

                    {/* Render the modal */}
                    <QuesitosModal
                        open={isModalOpen}
                        onClose={handleCloseModal}
                        title="Análise Gerada"
                        content={analiseResult || ''}
                    />
                </Stack>
        </Container>
    );
};

export default AnaliseDocsMedicos;
