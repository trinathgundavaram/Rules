# Rules Engine UI

React-based web interface for managing data validation rules and viewing results.

## Features

- Rule library management
- Visual rule builder
- Rule assignment to tables
- Validation results visualization
- Batch rule import
- Data source management

## Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## Environment Variables

Create `.env` file:

```
REACT_APP_API_URL=https://api.example.com
REACT_APP_COGNITO_USER_POOL_ID=us-east-1_xxxxx
REACT_APP_COGNITO_CLIENT_ID=xxxxx
REACT_APP_REGION=us-east-1
```

## Deployment

The UI is deployed to S3 and served via CloudFront. See [DEPLOYMENT.md](../../../DEPLOYMENT.md) for details.
