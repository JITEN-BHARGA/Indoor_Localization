"use client";

import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

type EspDevice = {
  device_id: string;
  device_name: string;
  is_active?: boolean;
};

type ScanResult = {
  object_id?: string;
  final_prediction?: string;
  final_method?: string;
  ml_result?: any;
  knn_result?: any;
  created_at?: string;
};

export default function Dashboard() {
  const [devices, setDevices] = useState<EspDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState("");
  const [requestId, setRequestId] = useState("");
  const [status, setStatus] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState("");

  const [newDeviceId, setNewDeviceId] = useState("");
  const [newDeviceName, setNewDeviceName] = useState("");

  async function loadDevices() {
    try {
      const res = await fetch(`${API_BASE}/esp-devices`, { cache: "no-store" });
      if (!res.ok) throw new Error("Failed to load devices");
      const data = await res.json();
      setDevices(data);
    } catch (err: any) {
      setError(err.message || "Failed to load devices");
    }
  }

  useEffect(() => {
    loadDevices();
  }, []);

  useEffect(() => {
    if (!requestId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/scan-requests/${requestId}`, {
          cache: "no-store",
        });
        if (!res.ok) throw new Error("Failed to fetch scan status");

        const data = await res.json();
        setStatus(data.status);

        if (data.status === "completed") {
          const resultRes = await fetch(
            `${API_BASE}/scan-requests/${requestId}/result`,
            { cache: "no-store" }
          );
          if (!resultRes.ok) throw new Error("Failed to fetch scan result");

          const resultData = await resultRes.json();
          setResult(resultData.result);
          clearInterval(interval);
        }

        if (data.status === "failed") {
          clearInterval(interval);
        }
      } catch (err: any) {
        setError(err.message || "Polling failed");
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [requestId]);

  async function createDevice() {
    if (!newDeviceId.trim() || !newDeviceName.trim()) {
      setError("Device ID and Device Name are required");
      return;
    }

    setError("");

    try {
      const res = await fetch(`${API_BASE}/esp-devices`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          device_id: newDeviceId.trim(),
          device_name: newDeviceName.trim(),
          is_active: true,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to create device");

      setNewDeviceId("");
      setNewDeviceName("");
      await loadDevices();
    } catch (err: any) {
      setError(err.message || "Failed to create device");
    }
  }

  async function startScan() {
    if (!selectedDevice) {
      setError("Select a device");
      return;
    }

    setError("");
    setResult(null);
    setStatus("");
    setRequestId("");

    try {
      const res = await fetch(`${API_BASE}/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          device_id: selectedDevice,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Scan failed");

      setRequestId(data.request_id);
      setStatus(data.status || "collecting");
    } catch (err: any) {
      setError(err.message || "Scan failed");
    }
  }

  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>Indoor Localization Dashboard</h1>

      {error && (
        <div
          style={{
            background: "#ffe5e5",
            color: "#900",
            padding: 12,
            borderRadius: 8,
            marginBottom: 16,
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
          marginBottom: 24,
        }}
      >
        <h2>Create ESP Device</h2>

        <div style={{ display: "grid", gap: 10 }}>
          <input
            type="text"
            placeholder="Device ID (example: esp32_01)"
            value={newDeviceId}
            onChange={(e) => setNewDeviceId(e.target.value)}
            style={{ padding: 10 }}
          />

          <input
            type="text"
            placeholder="Device Name / Object Name (example: Laptop Bag)"
            value={newDeviceName}
            onChange={(e) => setNewDeviceName(e.target.value)}
            style={{ padding: 10 }}
          />

          <button
            onClick={createDevice}
            style={{ padding: "10px 14px", cursor: "pointer", width: "fit-content" }}
          >
            Add ESP Device
          </button>
        </div>
      </section>

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
          marginBottom: 24,
        }}
      >
        <h2>Select Device</h2>

        <select
          value={selectedDevice}
          onChange={(e) => setSelectedDevice(e.target.value)}
          style={{ padding: 10, minWidth: 280 }}
        >
          <option value="">-- Select Device --</option>
          {devices.map((d) => (
            <option key={d.device_id} value={d.device_id}>
              {d.device_name} ({d.device_id})
            </option>
          ))}
        </select>

        <div style={{ marginTop: 14 }}>
          <button
            onClick={startScan}
            style={{ padding: "10px 14px", cursor: "pointer" }}
          >
            Start Scan
          </button>
        </div>
      </section>

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
          marginBottom: 24,
        }}
      >
        <h2>Available Devices</h2>

        {devices.length === 0 ? (
          <p>No devices found.</p>
        ) : (
          <div style={{ display: "grid", gap: 10 }}>
            {devices.map((d) => (
              <div
                key={d.device_id}
                style={{
                  border: "1px solid #eee",
                  borderRadius: 8,
                  padding: 12,
                }}
              >
                <div><strong>{d.device_name}</strong></div>
                <div>Device ID: {d.device_id}</div>
                <div>Status: {d.is_active === false ? "Inactive" : "Active"}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
        }}
      >
        <h2>Scan Status & Result</h2>

        {requestId && (
          <p><strong>Request ID:</strong> {requestId}</p>
        )}

        {status && (
          <p><strong>Status:</strong> {status}</p>
        )}

        {result && (
          <div
            style={{
              marginTop: 20,
              padding: 16,
              border: "1px solid #ddd",
              borderRadius: 10,
              background: "#f9f9f9",
            }}
          >
            <h3>📍 Final Prediction</h3>

            <p style={{ fontSize: 18 }}>
              <strong>Location:</strong>{" "}
              <span style={{ color: "#0070f3" }}>
                {result.final_prediction || "N/A"}
              </span>
            </p>

            <p>
              <strong>Method:</strong> {result.final_method || "N/A"}
            </p>

            {result.ml_result?.confidence && (
              <p>
                <strong>Confidence:</strong>{" "}
                {(result.ml_result.confidence * 100).toFixed(2)}%
              </p>
            )}

            <details style={{ marginTop: 10 }}>
              <summary>🔍 Show Full Details</summary>

              <div style={{ marginTop: 10 }}>
                <h4>ML Result</h4>
                <pre>{JSON.stringify(result.ml_result, null, 2)}</pre>

                <h4>KNN Result</h4>
                <pre>{JSON.stringify(result.knn_result, null, 2)}</pre>
              </div>
            </details>
          </div>
        )}
      </section>
    </main>
  );
}