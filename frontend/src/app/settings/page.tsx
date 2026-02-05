'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { getApiKey, setApiKey, clearApiKey, checkHealth } from '@/lib/api';
import { Check, AlertCircle, Loader2, Eye, EyeOff, Trash2 } from 'lucide-react';

export default function SettingsPage() {
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [savedKey, setSavedKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [status, setStatus] = useState<'checking' | 'connected' | 'error' | 'none'>('checking');
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    const key = getApiKey();
    setSavedKey(key);
    if (key) {
      checkConnection();
    } else {
      setStatus('none');
    }
  }, []);

  const checkConnection = async () => {
    setStatus('checking');
    try {
      const health = await checkHealth();
      setStatus('connected');
      setStatusMessage(`Connected - v${health.version}`);
    } catch (error) {
      setStatus('error');
      setStatusMessage('Failed to connect to API');
    }
  };

  const handleSaveKey = () => {
    if (apiKeyInput.trim()) {
      setApiKey(apiKeyInput.trim());
      setSavedKey(apiKeyInput.trim());
      setApiKeyInput('');
      checkConnection();
    }
  };

  const handleClearKey = () => {
    clearApiKey();
    setSavedKey(null);
    setStatus('none');
    setStatusMessage('');
  };

  const maskKey = (key: string) => {
    if (key.length <= 12) return key;
    return key.slice(0, 8) + '...' + key.slice(-4);
  };

  return (
    <div className="max-w-2xl mx-auto py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">
          Configure your ProofKit API connection
        </p>
      </div>

      {/* API Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle>API Connection</CardTitle>
          <CardDescription>
            Status of your connection to the ProofKit API
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            {status === 'checking' && (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                <span className="text-gray-600">Checking connection...</span>
              </>
            )}
            {status === 'connected' && (
              <>
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                <Badge variant="success">{statusMessage}</Badge>
              </>
            )}
            {status === 'error' && (
              <>
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <Badge variant="error">{statusMessage}</Badge>
              </>
            )}
            {status === 'none' && (
              <>
                <div className="w-3 h-3 bg-gray-300 rounded-full" />
                <span className="text-gray-500">No API key configured</span>
              </>
            )}
          </div>

          {status !== 'checking' && savedKey && (
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={checkConnection}
            >
              Test Connection
            </Button>
          )}
        </CardContent>
      </Card>

      {/* API Key Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>API Key</CardTitle>
          <CardDescription>
            Your API key for authenticating with the ProofKit API.
            Get your key by running <code className="bg-gray-100 px-1 rounded">proofkit api-key show</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {savedKey ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex-1 flex items-center gap-2">
                  <code className="flex-1 bg-gray-100 px-3 py-2 rounded text-sm font-mono">
                    {showKey ? savedKey : maskKey(savedKey)}
                  </code>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowKey(!showKey)}
                  >
                    {showKey ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                <Button
                  variant="destructive"
                  size="icon"
                  onClick={handleClearKey}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              <div className="text-sm text-gray-500">
                <Check className="w-4 h-4 inline mr-1 text-green-500" />
                API key is saved in your browser
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="apiKey">API Key</Label>
                <div className="flex gap-2">
                  <Input
                    id="apiKey"
                    type="password"
                    placeholder="pk_dev_..."
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                  />
                  <Button onClick={handleSaveKey} disabled={!apiKeyInput.trim()}>
                    Save
                  </Button>
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg text-sm">
                <p className="font-medium text-blue-800 mb-2">
                  How to get your API key:
                </p>
                <ol className="list-decimal list-inside space-y-1 text-blue-700">
                  <li>Start the ProofKit API server: <code className="bg-blue-100 px-1 rounded">proofkit serve</code></li>
                  <li>Get your API key: <code className="bg-blue-100 px-1 rounded">proofkit api-key show</code></li>
                  <li>Paste the key above</li>
                </ol>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* API Documentation */}
      <Card>
        <CardHeader>
          <CardTitle>API Documentation</CardTitle>
          <CardDescription>
            Learn more about the ProofKit API
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p>
              <strong>API Base URL:</strong>{' '}
              <code className="bg-gray-100 px-1 rounded">
                {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}
              </code>
            </p>
            <p>
              <strong>Interactive Docs:</strong>{' '}
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                http://localhost:8000/docs
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
