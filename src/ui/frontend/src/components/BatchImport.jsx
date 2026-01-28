import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  LinearProgress,
} from '@mui/material';
import { Upload as UploadIcon } from '@mui/icons-material';
import api from '../services/api';

const BatchImport = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      await api.batchImport(file);
      alert('Rules imported successfully!');
      setFile(null);
    } catch (error) {
      console.error('Import failed:', error);
      alert('Import failed. Please check the file format.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Batch Import Rules
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Upload CSV or Excel file
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          File should contain columns: rule_name, rule_type, rule_logic, severity, target_table, target_columns
        </Typography>

        <Box mt={2}>
          <input
            accept=".csv,.xlsx,.xls"
            style={{ display: 'none' }}
            id="file-upload"
            type="file"
            onChange={handleFileChange}
          />
          <label htmlFor="file-upload">
            <Button
              variant="outlined"
              component="span"
              startIcon={<UploadIcon />}
            >
              Select File
            </Button>
          </label>
          {file && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              Selected: {file.name}
            </Typography>
          )}
        </Box>

        {uploading && <LinearProgress sx={{ mt: 2 }} />}

        <Box mt={2}>
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            Upload and Import
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default BatchImport;
