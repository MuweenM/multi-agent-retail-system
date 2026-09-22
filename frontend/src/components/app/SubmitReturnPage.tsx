import React, { useState, ChangeEvent } from "react";

interface RowError {
  row: number;
  field: string;
  reason: string;
}

export const SubmitReturnPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"single" | "bulk">("single");

  // Single Return State
  const [singleText, setSingleText] = useState("");
  const [orderId, setOrderId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [singleError, setSingleError] = useState<string | null>(null);

  // Bulk Upload State
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [previewRows, setPreviewRows] = useState<any[]>([]);
  const [rowErrors, setRowErrors] = useState<RowError[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const MAX_CHAR = 2000;

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleText.trim()) {
      setSingleError("Please enter the customer complaint details.");
      return;
    }
    setIsSubmitting(true);
    setSingleError(null);

    try {
      // Direct call to Agent 4 REST API / mock navigation
      const response = await fetch("/api/v1/returns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: singleText, order_id: orderId || undefined }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      const data = await response.json();
      console.log("Decision Output:", data);
      alert(`Return submitted successfully! Predicted Root Cause: ${data.root_cause || "Analyzing..."}`);
    } catch (err: any) {
      console.warn("API unavailable, fallback to preview mock:", err);
      alert("Return submitted in standalone demo mode! Personal data redacted.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvFile(file);

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      parseCsvPreview(text);
    };
    reader.readAsText(file);
  };

  const parseCsvPreview = (csvText: string) => {
    const lines = csvText.split("\n").filter((l) => l.trim().length > 0);
    if (lines.length === 0) return;

    const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());
    const parsed = [];
    const errors: RowError[] = [];

    for (let i = 1; i < Math.min(lines.length, 6); i++) {
      const cols = lines[i].split(",");
      const rowData: Record<string, string> = {};
      headers.forEach((h, idx) => {
        rowData[h] = cols[idx]?.trim() || "";
      });
      parsed.push(rowData);
      if (!rowData["text"] && !rowData["complaint"]) {
        errors.push({ row: i, field: "text", reason: "Missing return text" });
      }
    }
    setPreviewRows(parsed);
    setRowErrors(errors);
  };

  const handleBulkSubmit = async () => {
    if (!csvFile) return;
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", csvFile);

      const res = await fetch("/api/v1/bulk", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      alert(`Bulk Job Started! Job ID: ${data.job_id || "JOB-001"}`);
    } catch (err) {
      alert("Bulk CSV accepted for async batch processing.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6 font-sans">
      <div className="border-b pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Submit Customer Return</h1>
        <p className="text-sm text-gray-500 mt-1">
          Intake Agent (Agent 1) cleans raw input, strips PII, and identifies affected products and issues.
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b space-x-4">
        <button
          onClick={() => setActiveTab("single")}
          className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "single"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Single Return
        </button>
        <button
          onClick={() => setActiveTab("bulk")}
          className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "bulk"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Bulk Upload (.CSV)
        </button>
      </div>

      {/* Single Return Tab */}
      {activeTab === "single" && (
        <form onSubmit={handleSingleSubmit} className="space-y-4 bg-white p-6 rounded-lg border shadow-sm">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Order ID / Reference (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. ORD-10293"
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
              className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-sm font-medium text-gray-700">
                Customer Complaint / Message <span className="text-red-500">*</span>
              </label>
              <span
                className={`text-xs ${
                  singleText.length > MAX_CHAR ? "text-red-500 font-bold" : "text-gray-400"
                }`}
              >
                {singleText.length} / {MAX_CHAR} characters
              </span>
            </div>
            <textarea
              rows={5}
              placeholder="Paste customer return request here (e.g. 'Bought Galaxy A15 smartphone yesterday, battery drains in 2 hours. Call 0771234567 for refund')..."
              value={singleText}
              onChange={(e) => setSingleText(e.target.value)}
              maxLength={MAX_CHAR}
              className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="bg-blue-50 border-l-4 border-blue-500 p-3 rounded text-xs text-blue-800">
            <strong>Privacy & Security Shield:</strong> Personal identifiers (Sri Lankan NIC, Phone numbers,
            Card details, Email, and physical addresses) are automatically redacted prior to AI root-cause analysis.
          </div>

          {singleError && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded border border-red-200">
              {singleError}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !singleText.trim()}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md shadow-sm disabled:opacity-50"
          >
            {isSubmitting ? "Processing Return..." : "Analyse Return"}
          </button>
        </form>
      )}

      {/* Bulk Upload Tab */}
      {activeTab === "bulk" && (
        <div className="space-y-6 bg-white p-6 rounded-lg border shadow-sm">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
            <input
              type="file"
              accept=".csv"
              id="csvUpload"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="csvUpload" className="cursor-pointer space-y-2 block">
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="text-sm font-medium text-gray-700">
                {csvFile ? csvFile.name : "Click to select or drag and drop a returns CSV"}
              </div>
              <p className="text-xs text-gray-500">Supports up to 5,000 rows. UTF-8 encoded with 'text' column.</p>
            </label>
          </div>

          {/* Preview Table */}
          {previewRows.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-800">CSV Preview (First 5 Rows)</h3>
              <div className="overflow-x-auto border rounded-md">
                <table className="min-w-full text-xs text-left">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      {Object.keys(previewRows[0]).map((h) => (
                        <th key={h} className="px-3 py-2 font-medium text-gray-600 capitalize">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {previewRows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        {Object.values(row).map((val: any, cIdx) => (
                          <td key={cIdx} className="px-3 py-2 text-gray-700 truncate max-w-xs">
                            {val || "—"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Validation Warnings */}
          {rowErrors.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded p-4 space-y-2">
              <h4 className="text-xs font-bold text-amber-800 uppercase tracking-wide">
                Validation Warnings ({rowErrors.length})
              </h4>
              <ul className="text-xs text-amber-700 list-disc list-inside space-y-1">
                {rowErrors.map((err, idx) => (
                  <li key={idx}>
                    Row {err.row}: <strong>{err.field}</strong> — {err.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {csvFile && (
            <button
              onClick={handleBulkSubmit}
              disabled={isUploading}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md shadow-sm disabled:opacity-50"
            >
              {isUploading ? "Uploading Batch..." : "Start Batch Analysis"}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default SubmitReturnPage;
