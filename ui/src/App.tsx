import React, { useState, useEffect } from 'react';
import { Send, Loader2, AlertCircle, FolderTree, RefreshCcw } from 'lucide-react';

interface ScanResult {
  id: string; // Scan ID extracted from container name
  containerName: string; // Full container name
  target: string; // Target URL
  result: any; // You can define a more specific type for results if needed
}

const TEMPLATE_CATEGORIES = [
  { id: 'cves', name: 'CVEs', description: 'Common Vulnerabilities and Exposures' },
  { id: 'vulnerabilities', name: 'Vulnerabilities', description: 'General security vulnerabilities' },
  { id: 'exposures', name: 'Exposures', description: 'Information exposures and leaks' },
  { id: 'technologies', name: 'Technologies', description: 'Technology detection templates' },
  { id: 'misconfiguration', name: 'Misconfigurations', description: 'Security misconfigurations' },
  { id: 'workflows', name: 'Workflows', description: 'Multi-step vulnerability workflows' },
  { id: 'default-logins', name: 'Default Logins', description: 'Default credential checks' },
  { id: 'exposed-panels', name: 'Exposed Panels', description: 'Exposed admin/service panels' },
  { id: 'takeovers', name: 'Takeovers', description: 'Subdomain takeover templates' },
  { id: 'file-upload', name: 'File Upload', description: 'File upload vulnerability checks' },
  { id: 'iot', name: 'IoT', description: 'Internet of Things vulnerabilities' },
];

function App() {
  const [target, setTarget] = useState('');
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>(['cves', 'vulnerabilities']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [currentScanId, setCurrentScanId] = useState<string>('');
  const [logs, setLogs] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (autoRefresh && currentScanId) {
      // Find the current scan to get the full container name
      const currentScan = scans.find(scan => scan.id === currentScanId);
      if (currentScan) {
        timer = setInterval(() => fetchLogs(currentScan.containerName), 5000);
      }
    }
    return () => clearInterval(timer); // Cleanup function to clear the interval
  }, [autoRefresh, currentScanId, scans]);

  const startScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://nuclei-api:8080/nuclei/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target,
          templates: selectedTemplates.map((t) => `${t}/`),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start scan');
      }

      const data = await response.json();
      const containerName = data.container_name;
      const scanId = containerName.match(/_(\d{6})$/)?.[1];

      if (scanId) {
        // Save scan details
        const newScan: ScanResult = {
          id: scanId,
          containerName: containerName,
          target: target, // Ensure target is saved here
          result: null, // You can add logic to store the result if available
        };
        setScans((prev) => [...prev, newScan]); // Save the scan in state
        fetchLogs(containerName); // Fetch logs for the new scan
      } else {
        throw new Error('Scan ID not found in container name');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start scan');
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async (containerName: string) => {
    try {
      const response = await fetch(`http://nuclei-api:8080/nuclei/scan/${containerName}/logs`);
      if (!response.ok) {
        throw new Error('Failed to fetch logs');
      }
      const data = await response.text();
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    }
  };

  const toggleTemplate = (templateId: string) => {
    setSelectedTemplates((prev) =>
      prev.includes(templateId) ? prev.filter((t) => t !== templateId) : [...prev, templateId]
    );
  };

  const switchScan = (scanId: string) => {
    const selectedScan = scans.find((scan) => scan.id === scanId);
    if (selectedScan) {
      setCurrentScanId(scanId);
      fetchLogs(selectedScan.containerName); // Fetch logs for the selected scan
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">Nuclei Scanner</h1>
        <div className="bg-gray-800 rounded-lg p-6 shadow-xl mb-8">
          <form onSubmit={startScan} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Target URL</label>
              <input
                type="url"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-4 py-2 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-3">
                <div className="flex items-center gap-2">
                  <FolderTree className="w-4 h-4" />
                  Select Templates
                </div>
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {TEMPLATE_CATEGORIES.map((template) => (
                  <div
                    key={template.id}
                    className={`p-3 rounded border cursor-pointer transition-colors ${
                      selectedTemplates.includes(template.id)
                        ? 'bg-blue-900/30 border-blue-500'
                        : 'bg-gray-700/30 border-gray-600 hover:border-gray-500'
                    }`}
                    onClick={() => toggleTemplate(template.id)}
                  >
                    <div className="font-medium">{template.name}</div>
                    <div className="text-sm text-gray-400">{template.description}</div>
                  </div>
                ))}
              </div>
            </div>
            <button
              type="submit"
              disabled={loading || selectedTemplates.length === 0}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /> Scanning...</>
              ) : (
                <><Send className="w-5 h-5" /> Start Scan</>
              )}
            </button>
          </form>
        </div>
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-8 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <p className="text-red-200">{error}</p>
          </div>
        )}
        {scans.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl mb-8">
            <h2 className="text-xl font-semibold mb-4">Saved Scans</h2>
            <div className="space-y-2">
              {scans.map((scan) => (
                <button
                  key={scan.id}
                  onClick={() => switchScan(scan.id)}
                  className={`w-full text-left px-4 py-2 rounded transition-colors ${
                    scan.id === currentScanId
                      ? 'bg-blue-900/30 border-blue-500'
                      : 'bg-gray-700/30 border-gray-600 hover:border-gray-500'
                  } border`}
                >
                  Scan ID: {scan.id} - Container: {scan.containerName} - Target: {scan.target}
                </button>
              ))}
            </div>
          </div>
        )}
        {currentScanId && (
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
            <h2 className="text-xl font-semibold mb-4">Logs</h2>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`mb-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded flex items-center gap-2 ${
                autoRefresh ? 'opacity-100' : 'opacity-75'
              }`}
            >
              <RefreshCcw className="w-5 h-5" />
              {autoRefresh ? 'Auto Refresh On' : 'Enable Auto Refresh'}
            </button>
            <pre className="bg-gray-900 rounded-lg p-4 text-sm overflow-auto">{logs || 'No logs available yet...'}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;