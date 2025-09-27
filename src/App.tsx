import { useState } from 'react';
import './index.css';

function App() {
  const [netlistFile, setNetlistFile] = useState<File | null>(null);
  const [bomFile, setBomFile] = useState<File | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [reIngest, setReIngest] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ message: string; downloadUrl?: string; error?: string, details?: string } | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!netlistFile) {
      setResult({ message: "", error: "Please select a Netlist file." });
      return;
    }

    setIsLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('netlist', netlistFile);
    if (bomFile) formData.append('bom', bomFile);
    if (imageFile) formData.append('layout_image', imageFile);
    formData.append('re_ingest', String(reIngest));

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'An unknown error occurred.', { cause: data.details });
      }

      setResult({ message: data.message, downloadUrl: data.downloadUrl });
    } catch (error: any) {
      setResult({ message: "", error: error.message, details: error.cause });
    } finally {
      setIsLoading(false);
    }
  };

  const FileInput = ({ label, required, onChange, accept }: { label: string, required?: boolean, onChange: (file: File | null) => void, accept: string }) => (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-300 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type="file"
        accept={accept}
        onChange={(e) => onChange(e.target.files ? e.target.files[0] : null)}
        className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-500 file:text-white hover:file:bg-blue-600"
      />
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-blue-400">AI PCB Test Plan Generator</h1>
          <p className="text-gray-400 mt-2">Upload your design files to automatically generate a bring-up test procedure.</p>
        </header>

        <main className="bg-gray-800 p-8 rounded-lg shadow-2xl">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FileInput label="Netlist File" required accept=".ipc,.txt" onChange={setNetlistFile} />
              <FileInput label="BOM File (Optional)" accept=".csv" onChange={setBomFile} />
            </div>
            <div className="mt-4">
              <FileInput label="Layout Image (Optional)" accept="image/png, image/jpeg" onChange={setImageFile} />
            </div>

            <div className="mt-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={reIngest}
                  onChange={(e) => setReIngest(e.target.checked)}
                  className="h-4 w-4 rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-600"
                />
                <span className="ml-2 text-sm text-gray-300">Force Re-ingestion of Source Documents</span>
              </label>
            </div>

            <div className="mt-8">
              <button
                type="submit"
                disabled={isLoading || !netlistFile}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white font-bold py-3 px-4 rounded-lg transition duration-300 ease-in-out disabled:cursor-not-allowed"
              >
                {isLoading ? 'Generating...' : 'Generate Test Plan'}
              </button>
            </div>
          </form>

          {result && (
            <div className="mt-8 p-4 rounded-lg bg-gray-700">
              {result.error && (
                <div>
                  <h3 className="font-bold text-red-500">Error</h3>
                  <p className="text-red-400">{result.error}</p>
                  {result.details && <pre className="mt-2 text-xs text-gray-400 bg-gray-800 p-2 rounded overflow-auto">{result.details}</pre>}
                </div>
              )}
              {result.downloadUrl && (
                <div>
                  <h3 className="font-bold text-green-500">Success!</h3>
                  <p className="text-green-300">{result.message}</p>
                  <a
                    href={result.downloadUrl}
                    download
                    className="mt-4 inline-block bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition"
                  >
                    Download Test Plan (.docx)
                  </a>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;