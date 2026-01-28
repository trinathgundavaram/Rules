import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  Paper,
} from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

const RuleBuilder = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    rule_name: '',
    rule_type: 'single_field',
    rule_category: '',
    severity_level: 'medium',
    rule_logic: '',
    is_reusable: true,
  });

  useEffect(() => {
    if (id) {
      fetchRule();
    }
  }, [id]);

  const fetchRule = async () => {
    try {
      const response = await api.getRule(id);
      setFormData(response.data);
    } catch (error) {
      console.error('Failed to fetch rule:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (id) {
        await api.updateRule(id, formData);
      } else {
        await api.createRule(formData);
      }
      navigate('/rules');
    } catch (error) {
      console.error('Failed to save rule:', error);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        {id ? 'Edit Rule' : 'Create New Rule'}
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Rule Name"
            value={formData.rule_name}
            onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
            required
            margin="normal"
          />

          <FormControl fullWidth margin="normal">
            <InputLabel>Rule Type</InputLabel>
            <Select
              value={formData.rule_type}
              onChange={(e) => setFormData({ ...formData, rule_type: e.target.value })}
            >
              <MenuItem value="single_field">Single Field</MenuItem>
              <MenuItem value="multi_field">Multi Field</MenuItem>
              <MenuItem value="cross_table">Cross Table</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Category"
            value={formData.rule_category}
            onChange={(e) => setFormData({ ...formData, rule_category: e.target.value })}
            margin="normal"
          />

          <FormControl fullWidth margin="normal">
            <InputLabel>Severity Level</InputLabel>
            <Select
              value={formData.severity_level}
              onChange={(e) => setFormData({ ...formData, severity_level: e.target.value })}
            >
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Rule Logic"
            value={formData.rule_logic}
            onChange={(e) => setFormData({ ...formData, rule_logic: e.target.value })}
            required
            multiline
            rows={6}
            margin="normal"
            placeholder="Enter SQL or Python expression, e.g., column IS NOT NULL"
          />

          <Box mt={3} display="flex" gap={2}>
            <Button type="submit" variant="contained">
              {id ? 'Update' : 'Create'} Rule
            </Button>
            <Button variant="outlined" onClick={() => navigate('/rules')}>
              Cancel
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default RuleBuilder;
