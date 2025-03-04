const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const { exec } = require('child_process');
const nmap = require('node-nmap');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Check if nmap is installed
let nmapInstalled = false;

// Function to check if nmap is installed
const checkNmapInstallation = () => {
  return new Promise((resolve) => {
    exec('which nmap', (error, stdout) => {
      if (error || !stdout) {
        console.log('nmap is not installed or not in PATH');
        resolve(false);
      } else {
        console.log('nmap is installed at:', stdout.trim());
        resolve(true);
      }
    });
  });
};

// Helper function to perform an nmap scan
const performScan = (target, options) => {
  return new Promise((resolve, reject) => {
    const scan = new nmap.NmapScan(target, options);
    scan.on('complete', (data) => {
      resolve(data);
    });
    scan.on('error', (error) => {
      reject(error);
    });
    scan.startScan();
  });
};

// Scan types mapping
const scanTypes = {
  'osAndPortScan': '-A', // Aggressive scan: OS detection, version detection, script scanning, traceroute
  'quickOsAndPorts': '-O -F -T4', // OS detection, fast port scan, aggressive timing
  'osOnly': '-O --osscan-limit -T4', // OS detection only, no port scan
  'portsOnly': '-F -T4', // Fast port scan only
};

// Routes

// API root endpoint
app.get('/api', (req, res) => {
  res.json({
    message: 'NMAP Fingerprinting Service API',
    nmapInstalled,
  });
});

// Scan a single IP address
app.post('/scan/ip', async (req, res) => {
  try {
    const { ip, scanType = 'quickOsAndPorts' } = req.body;
    if (!ip) return res.status(400).json({ error: 'IP address is required' });
    if (!nmapInstalled) return res.status(503).json({ error: 'nmap not installed' });

    const flags = scanTypes[scanType];
    if (!flags) return res.status(400).json({ error: 'Invalid scan type' });

    console.log(`Starting ${scanType} scan on ${ip} with flags: ${flags}`);
    const data = await performScan(ip, flags);
    res.json({ success: true, data });
  } catch (error) {
    console.error('Error in IP scan:', error);
    res.status(500).json({ success: false, error: error.toString() });
  }
});

// Custom scan with specific nmap arguments
app.post('/scan/custom', async (req, res) => {
  try {
    const { target, args } = req.body;

    if (!target || !args) {
      return res.status(400).json({ error: 'Both target and args are required' });
    }

    if (!nmapInstalled) {
      return res.status(503).json({ error: 'Service unavailable: nmap is not installed' });
    }

    console.log(`Starting custom scan on ${target} with args: ${args}`);
    const data = await performScan(target, args);
    res.json({ success: true, data });

  } catch (error) {
    console.error('Error processing custom scan request:', error);
    res.status(500).json({
      success: false,
      error: error.toString(),
    });
  }
});

// Start the server
const startServer = async () => {
  nmapInstalled = await checkNmapInstallation();

  if (!nmapInstalled) {
    console.error('Error: nmap is not installed. Please install it to run this server.');
    process.exit(10)
  }

  app.listen(PORT, () => {
    console.log(`NMAP Fingerprinting Service running on port ${PORT}`);
    console.log(`nmap installation status: ${nmapInstalled ? 'Installed' : 'Not installed'}`);
  });
};

startServer();