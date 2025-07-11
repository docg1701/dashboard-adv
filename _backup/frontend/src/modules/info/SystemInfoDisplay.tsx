// frontend/src/modules/info/SystemInfoDisplay.tsx
import React, { useState, useEffect } from 'react';
import { getSystemInfo, SystemInfoResponse } from '../../services/api'; // Import function and type
import { Box, CircularProgress, Typography, Alert, List, ListItem, ListItemText, Paper } from '@mui/material';

const SystemInfoDisplay: React.FC = () => {
  const [data, setData] = useState<SystemInfoResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await getSystemInfo();
        setData(result);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('An unknown error occurred while fetching system info.');
        }
        console.error("Error fetching system info:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []); // Empty dependency array means this effect runs once on mount

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 3 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading System Info...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Error loading system info: {error}
      </Alert>
    );
  }

  if (!data) {
    // Should not happen if loading is false and error is null, but good practice
    return <Typography>No system information available.</Typography>;
  }

  // Format the datetime string for better readability
  const formattedTime = data.server_time_utc
    ? new Date(data.server_time_utc).toLocaleString()
    : 'N/A';

  return (
    <Paper elevation={3} sx={{ p: 3 }}> {/* Use Paper for a contained look */}
      <Typography variant="h5" component="h2" gutterBottom>
        System Information
      </Typography>
      <List dense> {/* Use dense for tighter spacing */}
        <ListItem>
          <ListItemText primary="Environment" secondary={data.environment} />
        </ListItem>
        <ListItem>
          <ListItemText primary="Project Name" secondary={data.project_name} />
        </ListItem>
        <ListItem>
          <ListItemText primary="Server Time (UTC)" secondary={formattedTime} />
        </ListItem>
         <ListItem>
          <ListItemText primary="API Prefix" secondary={data.api_prefix} />
        </ListItem>
      </List>
    </Paper>
  );
};

export default SystemInfoDisplay;