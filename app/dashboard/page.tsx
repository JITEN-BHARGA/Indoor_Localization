"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

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

const COLORS = {
  pageBg: "#f5f7fb",
  cardBg: "#ffffff",
  border: "#dbe3ef",
  borderSoft: "#e7edf5",
  text: "#1f2937",
  textSoft: "#5b6472",
  primary: "#2563eb",
  primaryDark: "#1d4ed8",
  primarySoft: "#eff6ff",
  errorBg: "#fef2f2",
  errorBorder: "#fecaca",
  errorText: "#b91c1c",
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
    <main
      style={{
        padding: 24,
        maxWidth: 900,
        margin: "0 auto",
        background: COLORS.pageBg,
        minHeight: "100vh",
        color: COLORS.text,
      }}
    >
      <h1 style={{ color: COLORS.text, marginBottom: 20 }}>
        Indoor Localization Dashboard
      </h1>

      {error && (
        <div
          style={{
            background: COLORS.errorBg,
            color: COLORS.errorText,
            padding: 12,
            borderRadius: 8,
            marginBottom: 16,
            border: `1px solid ${COLORS.errorBorder}`,
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      <section
        style={{
          border: `1px solid ${COLORS.border}`,
          borderRadius: 10,
          padding: 16,
          marginBottom: 24,
          background: COLORS.cardBg,
          boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
        }}
      >
        <h2 style={{ marginTop: 0, color: COLORS.text }}>Create ESP Device</h2>

        <div style={{ display: "grid", gap: 10 }}>
          <input
            type="text"
            placeholder="Device ID (example: esp32_01)"
            value={newDeviceId}
            onChange={(e) => setNewDeviceId(e.target.value)}
            style={{
              padding: 10,
              borderRadius: 8,
              border: `1px solid ${COLORS.border}`,
              outline: "none",
              color: COLORS.text,
              background: "#fff",
            }}
          />

          <input
            type="text"
            placeholder="Device Name / Object Name (example: Laptop Bag)"
            value={newDeviceName}
            onChange={(e) => setNewDeviceName(e.target.value)}
            style={{
              padding: 10,
              borderRadius: 8,
              border: `1px solid ${COLORS.border}`,
              outline: "none",
              color: COLORS.text,
              background: "#fff",
            }}
          />

          <button
            onClick={createDevice}
            style={{
              padding: "10px 14px",
              cursor: "pointer",
              width: "fit-content",
              borderRadius: 8,
              border: "none",
              background: COLORS.primary,
              color: "#fff",
              fontWeight: 600,
            }}
          >
            Add ESP Device
          </button>
        </div>
      </section>

      <section
        style={{
          border: `1px solid ${COLORS.border}`,
          borderRadius: 10,
          padding: 16,
          marginBottom: 24,
          background: COLORS.cardBg,
          boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
        }}
      >
        <h2 style={{ marginTop: 0, color: COLORS.text }}>Select Device</h2>

        <select
          value={selectedDevice}
          onChange={(e) => setSelectedDevice(e.target.value)}
          style={{
            padding: 10,
            minWidth: 280,
            borderRadius: 8,
            border: `1px solid ${COLORS.border}`,
            outline: "none",
            color: COLORS.text,
            background: "#fff",
          }}
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
            style={{
              padding: "10px 14px",
              cursor: "pointer",
              borderRadius: 8,
              border: "none",
              background: COLORS.primary,
              color: "#fff",
              fontWeight: 600,
            }}
          >
            {status === "collecting" ? "Scanning..." : "Start Scan"}
          </button>
        </div>
      </section>

      <section
        style={{
          border: `1px solid ${COLORS.border}`,
          borderRadius: 10,
          padding: 16,
          marginBottom: 24,
          background: COLORS.cardBg,
          boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
        }}
      >
        <h2 style={{ marginTop: 0, color: COLORS.text }}>Available Devices</h2>

        {devices.length === 0 ? (
          <p style={{ color: COLORS.textSoft }}>No devices found.</p>
        ) : (
          <div style={{ display: "grid", gap: 10 }}>
            {devices.map((d) => (
              <div
                key={d.device_id}
                style={{
                  border: `1px solid ${COLORS.borderSoft}`,
                  borderRadius: 8,
                  padding: 12,
                  background: COLORS.primarySoft,
                }}
              >
                <div>
                  <strong style={{ color: COLORS.text }}>{d.device_name}</strong>
                </div>
                <div style={{ color: COLORS.textSoft }}>Device ID: {d.device_id}</div>
                <div style={{ color: COLORS.textSoft }}>
                  Status: {d.is_active === false ? "Inactive" : "Active"}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section
        style={{
          border: `1px solid ${COLORS.border}`,
          borderRadius: 10,
          padding: 16,
          background: COLORS.cardBg,
          boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
        }}
      >
        <h2 style={{ marginTop: 0, color: COLORS.text }}>Scan Status & Result</h2>

        {requestId && (
          <p style={{ color: COLORS.textSoft }}>
            <strong style={{ color: COLORS.text }}>Request ID:</strong> {requestId}
          </p>
        )}

        {status && (
          <p style={{ color: COLORS.textSoft }}>
            <strong style={{ color: COLORS.text }}>Status:</strong> {status}
          </p>
        )}

        {result && (
          <div
            style={{
              marginTop: 20,
              padding: 16,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 10,
              background: COLORS.primarySoft,
            }}
          >
            <h3 style={{ color: COLORS.primaryDark, marginTop: 0 }}>
              Final Prediction
            </h3>

            <p style={{ fontSize: 18, color: COLORS.text }}>
              <strong>Location:</strong>{" "}
              <span style={{ color: COLORS.primary }}>
                {result.final_prediction || "N/A"}
              </span>
            </p>

            <p style={{ color: COLORS.textSoft }}>
              <strong style={{ color: COLORS.text }}>Method:</strong>{" "}
              {result.final_method || "N/A"}
            </p>

            {result.ml_result?.confidence && (
              <p style={{ color: COLORS.textSoft }}>
                <strong style={{ color: COLORS.text }}>Confidence:</strong>{" "}
                {(result.ml_result.confidence * 100).toFixed(2)}%
              </p>
            )}

            <details style={{ marginTop: 10 }}>
              <summary style={{ color: COLORS.primaryDark, cursor: "pointer" }}>
                Show Full Details
              </summary>

              <div style={{ marginTop: 10 }}>
                <h4 style={{ color: COLORS.text }}>ML Result</h4>
                <pre
                  style={{
                    background: "#fff",
                    padding: 12,
                    borderRadius: 8,
                    border: `1px solid ${COLORS.borderSoft}`,
                    overflowX: "auto",
                    color: COLORS.text,
                  }}
                >
                  {JSON.stringify(result.ml_result, null, 2)}
                </pre>

                <h4 style={{ color: COLORS.text }}>KNN Result</h4>
                <pre
                  style={{
                    background: "#fff",
                    padding: 12,
                    borderRadius: 8,
                    border: `1px solid ${COLORS.borderSoft}`,
                    overflowX: "auto",
                    color: COLORS.text,
                  }}
                >
                  {JSON.stringify(result.knn_result, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        )}
      </section>
    </main>
  );
}