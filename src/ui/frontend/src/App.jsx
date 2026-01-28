import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Amplify } from 'aws-amplify';
import Dashboard from './components/Dashboard';
import RuleLibrary from './components/RuleLibrary';
import RuleBuilder from './components/RuleBuilder';
import RuleAssignment from './components/RuleAssignment';
import ValidationResults from './components/ValidationResults';
import BatchImport from './components/BatchImport';
import Layout from './components/Layout';

// Configure Amplify
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
      userPoolClientId: process.env.REACT_APP_COGNITO_CLIENT_ID,
      region: process.env.REACT_APP_REGION,
    }
  }
});

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/rules" element={<RuleLibrary />} />
            <Route path="/rules/new" element={<RuleBuilder />} />
            <Route path="/rules/:id/edit" element={<RuleBuilder />} />
            <Route path="/assignments" element={<RuleAssignment />} />
            <Route path="/results" element={<ValidationResults />} />
            <Route path="/import" element={<BatchImport />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
