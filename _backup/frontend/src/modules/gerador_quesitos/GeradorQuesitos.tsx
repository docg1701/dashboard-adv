// frontend/src/modules/gerador_quesitos/GeradorQuesitos.tsx
import React, { useState, useRef, ChangeEvent, useEffect } from 'react';
import {
    Box, Button, Typography, CircularProgress, Alert, Paper, Stack, Container,
    Input, List, ListItem, ListItemText, IconButton, Select, MenuItem,
    FormControl, InputLabel, SelectChangeEvent, Fade
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DeleteIcon from '@mui/icons-material/Delete';
import { OPCOES_BENEFICIO, OPCOES_PROFISSAO, FRASES_DIVERTIDAS } from '../../config/opcoesFormulario';
import { useGeradorQuesitosStore } from './geradorQuesitosStore';
import QuesitosModal from '../../components/common/QuesitosModal'; // Import the new modal

const GeradorQuesitos: React.FC = () => {
    // Local state
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [beneficio, setBeneficio] = useState<string>('');
    const [profissao, setProfissao] = useState<string>('');
    const [uiMessage, setUiMessage] = useState<string | null>(null);
    const [fraseDivertida, setFraseDivertida] = useState<string>('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false); // State for modal visibility

    // Global state from the simplified store
    const {
        isLoading,
        error,
        quesitosResult,
        gerarQuesitos,
        currentFileBeingProcessed,
        clearState, // Import clearState from the store
    } = useGeradorQuesitosStore();

    // Effect to open modal when results are ready
    useEffect(() => {
        if (quesitosResult && !isLoading) {
            setIsModalOpen(true);
        }
    }, [quesitosResult, isLoading]);

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
    const handleBeneficioChange = (event: SelectChangeEvent<string>) => { setBeneficio(event.target.value as string); };
    const handleProfissaoChange = (event: SelectChangeEvent<string>) => { setProfissao(event.target.value as string); };

    const handleGerarQuesitos = () => {
        setUiMessage(null);
        if (selectedFiles.length === 0) {
            setUiMessage("Nenhum arquivo PDF selecionado.");
            return;
        }
        if (selectedFiles.length > 1) {
            // setUiMessage("Apenas o primeiro arquivo PDF selecionado será processado.");
        }
        if (!beneficio) { setUiMessage("Por favor, selecione o benefício."); return; }
        if (!profissao) { setUiMessage("Por favor, selecione a profissão."); return; }

        const fileToProcess = selectedFiles[0];
        gerarQuesitos(fileToProcess, beneficio, profissao);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        clearState(); // Clear the result when modal is closed
    };

    return (
        <Container maxWidth="md" sx={{ mt: 4, mb: 4, p: 4, borderRadius: '12px', overflow: 'hidden' }}>
            <Stack spacing={3}>
                    <Typography variant="h5" component="h2" gutterBottom align="left" sx={{ fontWeight: 600, color: 'text.primary' }}>
                        Gerador de Quesitos para laudo pericial
                    </Typography>
            {!isLoading ? ( /* Inputs */ <>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                   <FormControl fullWidth required error={!!uiMessage && !beneficio}>
                       <InputLabel id="beneficio-select-label">Benefício Pretendido</InputLabel>
                       <Select labelId="beneficio-select-label" value={beneficio} label="Benefício Pretendido" onChange={handleBeneficioChange} disabled={isLoading}>
                           {OPCOES_BENEFICIO.map((option) => (<MenuItem key={option} value={option}>{option}</MenuItem>))}
                       </Select>
                   </FormControl>
                    <FormControl fullWidth required error={!!uiMessage && !profissao}>
                       <InputLabel id="profissao-select-label">Profissão</InputLabel>
                       <Select labelId="profissao-select-label" value={profissao} label="Profissão" onChange={handleProfissaoChange} disabled={isLoading}>
                           {OPCOES_PROFISSAO.map((option) => (<MenuItem key={option} value={option}>{option}</MenuItem>))}
                       </Select>
                   </FormControl>
                </Stack>
               <Box sx={{ textAlign: 'center', p: 2, border: '2px dashed', borderColor: 'grey.400', borderRadius: '8px', bgcolor: 'grey.50' }}>
                            <Button variant="contained" onClick={handleUploadClick} startIcon={<UploadFileIcon />} disabled={isLoading} size="large">
                                Adicionar PDF(s)
                            </Button>
                            <Input type="file" inputRef={fileInputRef} onChange={handleFileChange} inputProps={{ accept: '.pdf', multiple: true, 'data-testid': 'file-input-gerador-quesitos' }} sx={{ display: 'none' }} />
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                Arraste e solte seus arquivos PDF aqui, ou clique para selecionar.
                            </Typography>
                        </Box>
            </> ) : ( /* Loading State Display */
                <Paper elevation={0} sx={{ p: 3, textAlign: 'center', bgcolor: 'action.hover', borderRadius: '8px' }}>
                    <Typography variant="h6" component="p" gutterBottom>
                        {currentFileBeingProcessed ? `Processando: ${currentFileBeingProcessed.name}` : "Aguardando Ação..."}
                    </Typography>
                    <Typography variant="body1" color="text.secondary"> Benefício: {beneficio} </Typography>
                    <Typography variant="body1" color="text.secondary"> Profissão: {profissao} </Typography>
                </Paper>
            )}
            {selectedFiles.length > 0 && ( /* File List */
                <Paper variant="outlined" sx={{ p: 2, mt: 2, maxHeight: '250px', overflowY: 'auto', borderRadius: '8px', borderColor: 'grey.300' }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ mb: 1, fontWeight: 500 }}>
                        Arquivos Selecionados:
                    </Typography>
                <List dense>
                    {selectedFiles.map((file, index) => (
                        <ListItem key={`${file.name}-${index}-${file.lastModified}`} secondaryAction={ <IconButton edge="end" aria-label="delete" onClick={() => handleRemoveFile(index)} disabled={isLoading}> <DeleteIcon fontSize="small"/> </IconButton> } sx={{py: 0}}>
                            <ListItemText primary={file.name} secondary={`${(file.size / 1024).toFixed(1)} KB`} primaryTypographyProps={{ sx: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }} />
                        </ListItem>
                    ))}
                </List>
            </Paper> )}
             {uiMessage && !isLoading && (
                        <Alert severity={uiMessage.includes('duplicado') || uiMessage.includes('ignorados') ? 'info' : 'warning'} sx={{ mt: 2, borderRadius: '8px' }}>
                            {uiMessage}
                        </Alert>
                    )}
            <Box sx={{ textAlign: 'center', mt: 3 }}> {/* Submit Button */}
                        <Button variant="contained" color="primary" onClick={handleGerarQuesitos} disabled={isLoading || selectedFiles.length === 0 || !beneficio || !profissao} sx={{ minWidth: '180px', px: 3, py: 1.5, fontSize: '1rem' }}>
                            {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Gerar Quesitos'}
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
                title="Quesitos Gerados"
                content={quesitosResult || ''}
            />
        </Stack>
        </Container>
    );
};

export default GeradorQuesitos;
