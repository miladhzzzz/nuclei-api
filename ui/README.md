# Nuclei API with Queue System

A secure API wrapper for Nuclei vulnerability scanner with queue-based processing.

## Features

- Secure API endpoints with JWT authentication
- Rate limiting to prevent abuse
- Queue-based scan processing using Bull
- Input validation and sanitization
- Error handling and logging
- Asynchronous scan execution

## Prerequisites

- Node.js
- Redis server
- Nuclei installed on the system

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables in `.env`

3. Start the server:
```bash
npm run start:api
```

## API Endpoints

### POST /api/scan
Start a new scan

Request:
```json
{
  "target": "https://example.com",
  "templates": ["cves/", "vulnerabilities/"]
}
```

### GET /api/scan/:jobId
Get scan status and results

## Security Considerations

- All requests require JWT authentication
- Rate limiting is enabled
- Input validation for all parameters
- Secure headers with Helmet
- CORS protection
- Queue-based processing to prevent DoS