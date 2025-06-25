import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Button,
  Paper,
  Box,
  CircularProgress,
  Alert,
  TextField,
  Grid,
} from '@mui/material';
import { useSnackbar } from 'notistack';
// Import postDocumentQuery and its related types
import {
  uploadDocumentForAnalysis,
  getTaskStatus,
  postDocumentQuery, // Added
  DocumentUploadResponse,
  TaskStatusResponse,
  DocumentQueryPayload, // Added
  DocumentQueryResponse // Added
} from '../../services/api'; // Adjust path as needed

const TranscritorPdfTesterPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [processedFilename, setProcessedFilename] = useState<string | null>(null); // For storing the name of the processed file
  const [transcriptionStatus, setTranscriptionStatus] = useState<string | null>(null);
  const [transcriptionResult, setTranscriptionResult] = useState<string | null>(null);
  const [pollingError, setPollingError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isPolling, setIsPolling] = useState<boolean>(false);

  // State for query functionality
  const [query, setQuery] = useState<string>('');
  const [queryResult, setQueryResult] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [isQuerying, setIsQuerying] = useState<boolean>(false);

  const { enqueueSnackbar } = useSnackbar();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      setUploadStatus('idle');
      setUploadError(null);
      setTaskId(null);
      setTranscriptionStatus(null);
      setTranscriptionResult(null);
      setPollingError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      enqueueSnackbar('Please select a PDF file first.', { variant: 'warning' });
      return;
    }

    setIsUploading(true);
    setUploadStatus('uploading');
    setUploadError(null);
    setTaskId(null); // Reset previous task ID

    try {
      const response: DocumentUploadResponse = await uploadDocumentForAnalysis(selectedFile);
      setUploadStatus('success');
      enqueueSnackbar(response.message || 'File uploaded successfully! Transcription started.', { variant: 'success' });
      if (response.transcriber_data && response.transcriber_data.task_id && selectedFile) {
        setTaskId(response.transcriber_data.task_id);
        setProcessedFilename(selectedFile.name); // Store the filename
        // Reset query states for new upload
        setQuery('');
        setQueryResult(null);
        setQueryError(null);
      } else {
        setUploadStatus('error');
        setUploadError('Task ID not found in upload response or file not selected.');
        enqueueSnackbar('Task ID not found in upload response.', { variant: 'error' });
      }
    } catch (error: any) {
      setUploadStatus('error');
      const errorMessage = error.message || 'File upload failed.';
      setUploadError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
    } finally {
      setIsUploading(false);
    }
  };

  // useCallback to memoize poll function
  const pollStatus = useCallback(async (currentTaskId: string) => {
    try {
      const statusResponse: TaskStatusResponse = await getTaskStatus(currentTaskId);
      setTranscriptionStatus(statusResponse.status);

      if (statusResponse.status === 'SUCCESS') {
        setTranscriptionResult(JSON.stringify(statusResponse.result, null, 2) || 'Transcription successful, but no result content.');
        enqueueSnackbar('Transcription completed successfully!', { variant: 'success' });
        return true; // Stop polling
      } else if (statusResponse.status === 'FAILURE') {
        setPollingError(statusResponse.error_info?.error || 'Transcription failed for an unknown reason.');
        setTranscriptionResult(JSON.stringify(statusResponse.error_info, null, 2) || 'Failure details unavailable.');
        enqueueSnackbar('Transcription failed.', { variant: 'error' });
        return true; // Stop polling
      }
      return false; // Continue polling
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch transcription status.';
      setPollingError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      return true; // Stop polling on error
    }
  }, [enqueueSnackbar]);


  useEffect(() => {
    let intervalId: NodeJS.Timeout | undefined = undefined;

    if (taskId && (transcriptionStatus !== 'SUCCESS' && transcriptionStatus !== 'FAILURE')) {
      setIsPolling(true);
      // Initial poll
      pollStatus(taskId).then(stop => {
        if (stop) setIsPolling(false);
      });

      intervalId = setInterval(async () => {
        const stopPolling = await pollStatus(taskId);
        if (stopPolling) {
          clearInterval(intervalId);
          setIsPolling(false);
        }
      }, 5000); // Poll every 5 seconds
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
      setIsPolling(false); // Ensure polling stops on cleanup
    };
  }, [taskId, pollStatus, transcriptionStatus]);

  const handleQuerySubmit = async () => {
    if (!processedFilename || !query.trim()) {
      enqueueSnackbar('No document processed or query is empty.', { variant: 'warning' });
      return;
    }

    setIsQuerying(true);
    setQueryError(null);
    setQueryResult(null);

    try {
      const payload: DocumentQueryPayload = { user_query: query }; // Changed query_text to user_query
      // The documentId for postDocumentQuery is the filename, which is stored in processedFilename.
      // The backend /documents/query/{document_id} endpoint (proxied) ultimately maps to
      // transcritor-pdf's /query-document/{document_filename}
      const response: DocumentQueryResponse = await postDocumentQuery(processedFilename, payload);

      // The DocumentQueryResponse interface in api.ts expects:
      // { answer: string; query_id: string; } (query_id is optional based on actual transcritor response)
      // The actual response from transcritor-pdf /query-document is:
      // {"document_id": string, "query": string, "answer": string}
      // So, response.answer should be directly usable.
      if (response && typeof response.answer === 'string') {
        setQueryResult(response.answer);
        enqueueSnackbar('Query successful!', { variant: 'success' });
      } else {
        setQueryError("Received an unexpected response format from the query endpoint.");
        setQueryResult(JSON.stringify(response, null, 2)); // Show what was received
        enqueueSnackbar('Unexpected response format from query.', { variant: 'error' });
      }

    } catch (error: any) {
      const errorMessage = error.message || 'Failed to submit query.';
      setQueryError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Transcritor PDF Tester
        </Typography>

        <Grid container spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <Grid item xs={12} sm={8}>
            <TextField
              type="file"
              onChange={handleFileChange}
              fullWidth
              variant="outlined"
              size="small"
              InputLabelProps={{ shrink: true }}
              inputProps={{ accept: '.pdf' }}
              label={selectedFile ? selectedFile.name : "Select PDF File"}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleUpload}
              disabled={!selectedFile || isUploading || isPolling}
              fullWidth
              startIcon={isUploading ? <CircularProgress size={20} color="inherit" /> : null}
            >
              {isUploading ? 'Uploading...' : 'Upload & Transcribe'}
            </Button>
          </Grid>
        </Grid>

        {uploadStatus === 'error' && uploadError && (
          <Alert severity="error" sx={{ mb: 2 }}>{uploadError}</Alert>
        )}

        {taskId && (
          <Box sx={{ mt: 2, p: 2, border: '1px dashed grey', borderRadius: 1 }}>
            <Typography variant="h6">Transcription Progress</Typography>
            <Typography variant="body2">Task ID: {taskId}</Typography>
            <Typography variant="body2">
              Status: {transcriptionStatus || 'Fetching status...'}
              {isPolling && <CircularProgress size={16} sx={{ ml: 1 }} />}
            </Typography>
            {pollingError && (
              <Alert severity="error" sx={{ mt: 1 }}>Polling Error: {pollingError}</Alert>
            )}
          </Box>
        )}

        {transcriptionResult && (
          <Box sx={{ mt: 2, p: 2, border: '1px solid green', borderRadius: 1 }}>
            <Typography variant="h6">Transcription Result</Typography>
            <TextField
              value={transcriptionResult}
              multiline
              fullWidth
              rows={10}
              variant="outlined"
              InputProps={{ readOnly: true }}
              sx={{ mt: 1, fontFamily: 'monospace' }}
            />
          </Box>
        )}

        {/* Query Section - Appears after successful transcription */}
        {processedFilename && transcriptionStatus === 'SUCCESS' && (
          <Box sx={{ mt: 4, p: 2, border: '1px solid blue', borderRadius: 1 }}>
            <Typography variant="h6" gutterBottom>
              Query Document: {processedFilename}
            </Typography>
            <TextField
              label="Enter your query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              fullWidth
              variant="outlined"
              size="small"
              sx={{ mb: 1 }}
            />
            <Button
              variant="contained"
              color="secondary"
              onClick={handleQuerySubmit}
              disabled={!query.trim() || isQuerying || isPolling}
              startIcon={isQuerying ? <CircularProgress size={20} color="inherit" /> : null}
            >
              {isQuerying ? 'Querying...' : 'Submit Query'}
            </Button>

            {isQuerying && <CircularProgress size={24} sx={{ display: 'block', mt: 2, mx: 'auto' }} />}

            {queryError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                Query Error: {queryError}
              </Alert>
            )}
            {queryResult && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1">Query Answer:</Typography>
                <Paper elevation={2} sx={{ p: 2, mt: 1, maxHeight: '200px', overflowY: 'auto', whiteSpace: 'pre-wrap', backgroundColor: '#f9f9f9' }}>
                  {queryResult}
                </Paper>
              </Box>
            )}
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default TranscritorPdfTesterPage;
