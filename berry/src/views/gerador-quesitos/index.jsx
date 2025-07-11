import { useState, useRef, useEffect } from 'react';
import {
    Box, Button, Typography, CircularProgress, Alert, Paper, Stack,
    Input, List, ListItem, ListItemText, IconButton, Select, MenuItem,
    FormControl, InputLabel, Fade
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DeleteIcon from '@mui/icons-material/Delete';

// project imports
import MainCard from 'ui-component/cards/MainCard';
import QuesitosModal from 'ui-component/QuesitosModal';
import { OPCOES_BENEFICIO, OPCOES_PROFISSAO, FRASES_DIVERTIDAS } from 'config/opcoesFormulario';
import { useGeradorQuesitosStore } from 'stores/modules/gerador_quesitos/geradorQuesitosStore';

// ==============================|| GERADOR DE QUESITOS PAGE ||============================== //

const GeradorQuesitosPage = () => {
    // Local state
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [beneficio, setBeneficio] = useState('');
    const [profissao, setProfissao] = useState('');
    const [uiMessage, setUiMessage] = useState(null);
    const [fraseDivertida, setFraseDivertida] = useState('');
    const fileInputRef = useRef(null);
    const intervalRef = useRef(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Global state from store
    const {
        isLoading,
        error,
        quesitosResult,
        gerarQuesitos,
        currentFileBeingProcessed,
        clearState,
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
    const handleFileChange = (event) => {
        const files = event.target.files;
        let newFilesToAdd = [];
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
    const handleRemoveFile = (indexToRemove) => { setSelectedFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToRemove)); };
    const handleBeneficioChange = (event) => { setBeneficio(event.target.value); };
    const handleProfissaoChange = (event) => { setProfissao(event.target.value); };

    const handleGerarQuesitos = () => {
        setUiMessage(null);
        if (selectedFiles.length === 0) {
            setUiMessage("Nenhum arquivo PDF selecionado.");
            return;
        }
        if (!beneficio) { setUiMessage("Por favor, selecione o benefício."); return; }
        if (!profissao) { setUiMessage("Por favor, selecione a profissão."); return; }

        const fileToProcess = selectedFiles[0];
        gerarQuesitos(fileToProcess, beneficio, profissao);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        clearState();
    };

    return (
        <MainCard title="Gerador de Quesitos para Laudo Pericial">
            <Stack spacing={3}>
                {!isLoading ? (
                    <>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                            <FormControl fullWidth required error={!!uiMessage && !beneficio}>
                                <InputLabel>Benefício Pretendido</InputLabel>
                                <Select value={beneficio} label="Benefício Pretendido" onChange={handleBeneficioChange}>
                                    {OPCOES_BENEFICIO.map((option) => (<MenuItem key={option} value={option}>{option}</MenuItem>))}
                                </Select>
                            </FormControl>
                            <FormControl fullWidth required error={!!uiMessage && !profissao}>
                                <InputLabel>Profissão</InputLabel>
                                <Select value={profissao} label="Profissão" onChange={handleProfissaoChange}>
                                    {OPCOES_PROFISSAO.map((option) => (<MenuItem key={option} value={option}>{option}</MenuItem>))}
                                </Select>
                            </FormControl>
                        </Stack>
                        <Box sx={{ textAlign: 'center', p: 2, border: '2px dashed', borderColor: 'grey.400', borderRadius: 1, bgcolor: 'grey.50' }}>
                            <Button variant="contained" onClick={handleUploadClick} startIcon={<UploadFileIcon />} size="large">
                                Adicionar PDF(s)
                            </Button>
                            <Input type="file" inputRef={fileInputRef} onChange={handleFileChange} inputProps={{ accept: '.pdf', multiple: true }} sx={{ display: 'none' }} />
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                Arraste e solte seus arquivos PDF aqui, ou clique para selecionar.
                            </Typography>
                        </Box>
                    </>
                ) : (
                    <Paper elevation={0} sx={{ p: 3, textAlign: 'center', bgcolor: 'action.hover', borderRadius: 1 }}>
                        <Typography variant="h6" component="p" gutterBottom>
                            {currentFileBeingProcessed ? `Processando: ${currentFileBeingProcessed.name}` : "Aguardando Ação..."}
                        </Typography>
                        <Typography variant="body1" color="text.secondary"> Benefício: {beneficio} </Typography>
                        <Typography variant="body1" color="text.secondary"> Profissão: {profissao} </Typography>
                    </Paper>
                )}

                {selectedFiles.length > 0 && (
                    <Paper variant="outlined" sx={{ p: 2, mt: 2, maxHeight: '250px', overflowY: 'auto', borderRadius: 1 }}>
                        <Typography variant="subtitle1" gutterBottom sx={{ mb: 1, fontWeight: 500 }}>
                            Arquivos Selecionados:
                        </Typography>
                        <List dense>
                            {selectedFiles.map((file, index) => (
                                <ListItem key={`${file.name}-${index}-${file.lastModified}`} secondaryAction={<IconButton edge="end" onClick={() => handleRemoveFile(index)} disabled={isLoading}><DeleteIcon fontSize="small" /></IconButton>} sx={{ py: 0 }}>
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

                <Box sx={{ textAlign: 'center', mt: 3 }}>
                    <Button variant="contained" color="secondary" onClick={handleGerarQuesitos} disabled={isLoading || selectedFiles.length === 0 || !beneficio || !profissao} sx={{ minWidth: '180px', px: 3, py: 1.5, fontSize: '1rem' }}>
                        {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Gerar Quesitos'}
                    </Button>
                </Box>

                {isLoading && (
                    <Fade in={!!fraseDivertida} timeout={300}>
                        <Box>
                            <Typography variant="body1" align="center" sx={{ mt: 1, fontStyle: 'italic', display: 'block', minHeight: '1.5em' }}>
                                {fraseDivertida || '\u00A0'}
                            </Typography>
                        </Box>
                    </Fade>
                )}

                {error && (<Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>)}

                <QuesitosModal
                    open={isModalOpen}
                    onClose={handleCloseModal}
                    title="Quesitos Gerados"
                    content={quesitosResult || ''}
                />
            </Stack>
        </MainCard>
    );
};

export default GeradorQuesitosPage;
