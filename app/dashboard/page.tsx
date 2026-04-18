"use client";

import { useEffect, useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

type ObjectItem = {
  object_id: string;
  name: string;
  description?: string | null;
  created_at?: string | null;
};

type EspDevice = {
  device_id: string;
  device_name: string;
  is_active: boolean;
  last_seen_at?: string | null;
};

type ScanRequestStatus = {
  request_id: string;
  object_id: string;
  status: string;
  requested_at?: string | null;
  completed_at?: string | null;
  expected_device_count: number;
  received_device_count: number;
  device_statuses: { device_id: string; status: string }[];
};

type PredictionResult = {
  object_id: string;
  final_prediction: string;
  final_method: string;
  ml_result: {
    predicted_location?: string;
    confidence?: number;
    top_k?: { location: string; score: number }[];
  };
  knn_result: {
    predicted_location?: string;
    k?: number;
    top_matches?: {
      location: string;
      sequence_number: number;
      similarity_score: number;
      common_mac_count: number;
    }[];
  };
  created_at?: string;
};

export default function DashboardPage() {
  const [objects, setObjects] = useState<ObjectItem[]>([]);
  const [devices, setDevices] = useState<EspDevice[]>([]);
  const [selectedObjectId, setSelectedObjectId] = useState<string>("");
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<string[]>([]);
  const [requestId, setRequestId] = useState<string>("");
  const [requestStatus, setRequestStatus] = useState<ScanRequestStatus | null>(null);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [error, setError] = useState<string>("");

  const [newObjectId, setNewObjectId] = useState("");
  const [newObjectName, setNewObjectName] = useState("");
  const [newObjectDescription, setNewObjectDescription] = useState("");

  const [newEspId, setNewEspId] = useState("");
  const [newEspName, setNewEspName] = useState("");

  const selectedObject = useMemo(
    () => objects.find((obj) => obj.object_id === selectedObjectId) || null,
    [objects, selectedObjectId]
  );

  async function fetchObjects() {
    const res = await fetch(`${API_BASE}/objects`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to fetch objects: ${res.status}`);
    const data = await res.json();
    setObjects(data);
  }

  async function fetchEspDevices() {
    const res = await fetch(`${API_BASE}/esp-devices`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to fetch ESP devices: ${res.status}`);
    const data = await res.json();
    setDevices(data);
  }

  async function createObject() {
    setError("");
    const res = await fetch(`${API_BASE}/objects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        object_id: newObjectId,
        name: newObjectName,
        description: newObjectDescription || null,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || "Failed to create object");
    }

    setNewObjectId("");
    setNewObjectName("");
    setNewObjectDescription("");
    await fetchObjects();
  }

  async function createEspDevice() {
    setError("");
    const res = await fetch(`${API_BASE}/esp-devices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_id: newEspId,
        device_name: newEspName,
        is_active: true,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || "Failed to create ESP device");
    }

    setNewEspId("");
    setNewEspName("");
    await fetchEspDevices();
  }

  async function startScan() {
    if (!selectedObjectId) {
      setError("Please select an object");
      return;
    }

    if (selectedDeviceIds.length === 0) {
      setError("Please select at least one ESP device");
      return;
    }

    setError("");
    setResult(null);
    setRequestStatus(null);

    const res = await fetch(`${API_BASE}/scan`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        object_id: selectedObjectId,
        device_ids: selectedDeviceIds,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || "Failed to start scan");
    }

    const data = await res.json();
    setRequestId(data.request_id);
  }

  async function pollRequestStatus(activeRequestId: string) {
    const res = await fetch(`${API_BASE}/scan-requests/${activeRequestId}`, {
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error(`Failed to fetch request status: ${res.status}`);
    }

    const data = await res.json();
    setRequestStatus(data);

    if (data.status === "completed") {
      const resultRes = await fetch(`${API_BASE}/scan-requests/${activeRequestId}/result`, {
        cache: "no-store",
      });

      if (resultRes.ok) {
        const resultJson = await resultRes.json();
        setResult(resultJson.result);
      }
    }
  }

  function toggleDevice(deviceId: string) {
    setSelectedDeviceIds((prev) =>
      prev.includes(deviceId)
        ? prev.filter((id) => id !== deviceId)
        : [...prev, deviceId]
    );
  }

  useEffect(() => {
    async function init() {
      try {
        await Promise.all([fetchObjects(), fetchEspDevices()]);
      } catch (err: any) {
        setError(err.message || "Initial load failed");
      }
    }
    init();
  }, []);

  useEffect(() => {
    if (!requestId) return;

    pollRequestStatus(requestId).catch((err) => {
      setError(err.message || "Polling failed");
    });

    const timer = setInterval(() => {
      pollRequestStatus(requestId).catch((err) => {
        setError(err.message || "Polling failed");
      });
    }, 2000);

    return () => clearInterval(timer);
  }, [requestId]);

  return (
    <main style={{ padding: 24, maxWidth: 1200, margin: "0 auto" }}>
      <h1>Indoor Localization Dashboard</h1>

      {error && (
        <div style={{ background: "#fee", color: "#900", padding: 12, marginBottom: 16 }}>
          {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 10 }}>
          <h2>Create Object</h2>
          <input
            placeholder="Object ID"
            value={newObjectId}
            onChange={(e) => setNewObjectId(e.target.value)}
            style={{ width: "100%", padding: 8, marginBottom: 8 }}
          />
          <input
            placeholder="Object Name"
            value={newObjectName}
            onChange={(e) => setNewObjectName(e.target.value)}
            style={{ width: "100%", padding: 8, marginBottom: 8 }}
          />
          <input
            placeholder="Description"
            value={newObjectDescription}
            onChange={(e) => setNewObjectDescription(e.target.value)}
            style={{ width: "100%", padding: 8, marginBottom: 8 }}
          />
          <button onClick={createObject} style={{ padding: "10px 14px" }}>
            Save Object
          </button>
        </section>

        <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 10 }}>
          <h2>Create ESP Device</h2>
          <input
            placeholder="ESP Device ID"
            value={newEspId}
            onChange={(e) => setNewEspId(e.target.value)}
            style={{ width: "100%", padding: 8, marginBottom: 8 }}
          />
          <input
            placeholder="ESP Device Name"
            value={newEspName}
            onChange={(e) => setNewEspName(e.target.value)}
            style={{ width: "100%", padding: 8, marginBottom: 8 }}
          />
          <button onClick={createEspDevice} style={{ padding: "10px 14px" }}>
            Save ESP Device
          </button>
        </section>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginTop: 24 }}>
        <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 10 }}>
          <h2>Objects</h2>
          {objects.length === 0 ? (
            <p>No objects found</p>
          ) : (
            objects.map((obj) => (
              <label
                key={obj.object_id}
                style={{
                  display: "block",
                  padding: 10,
                  marginBottom: 8,
                  border: "1px solid #ddd",
                  borderRadius: 8,
                  background: selectedObjectId === obj.object_id ? "#eef6ff" : "#fff",
                  cursor: "pointer",
                }}
              >
                <input
                  type="radio"
                  name="selectedObject"
                  checked={selectedObjectId === obj.object_id}
                  onChange={() => setSelectedObjectId(obj.object_id)}
                  style={{ marginRight: 8 }}
                />
                <strong>{obj.name}</strong> ({obj.object_id})
                <div style={{ color: "#666", fontSize: 14 }}>{obj.description || "-"}</div>
              </label>
            ))
          )}
        </section>

        <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 10 }}>
          <h2>Select ESP Devices</h2>
          {devices.length === 0 ? (
            <p>No ESP devices found</p>
          ) : (
            devices.map((dev) => (
              <label
                key={dev.device_id}
                style={{
                  display: "block",
                  padding: 10,
                  marginBottom: 8,
                  border: "1px solid #ddd",
                  borderRadius: 8,
                  background: selectedDeviceIds.includes(dev.device_id) ? "#eef6ff" : "#fff",
                  cursor: "pointer",
                  opacity: dev.is_active ? 1 : 0.5,
                }}
              >
                <input
                  type="checkbox"
                  checked={selectedDeviceIds.includes(dev.device_id)}
                  disabled={!dev.is_active}
                  onChange={() => toggleDevice(dev.device_id)}
                  style={{ marginRight: 8 }}
                />
                <strong>{dev.device_name}</strong> ({dev.device_id})
                <div style={{ color: "#666", fontSize: 14 }}>
                  Status: {dev.is_active ? "Active" : "Inactive"}
                </div>
              </label>
            ))
          )}
        </section>
      </div>

      <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 10, marginTop: 24 }}>
        <h2>Scan Control</h2>
        <p><strong>Selected Object:</strong> {selectedObject ? `${selectedObject.name} (${selectedObject.object_id})` : "-"}</p>
        <p><strong>Selected ESP Count:</strong> {selectedDeviceIds.length}</p>

        <button onClick={startScan} style={{ padding: "12px 18px", fontSize: 16 }}>
          Start Scan
        </button>

        {requestId && (
          <div style={{ marginTop: 16 }}>
            <p><strong>Request ID:</strong> {requestId}</p>
          </div>
        )}
      </section>

      {requestStatus && (
        <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 10, marginTop: 24 }}>
          <h2>Scan Request Status</h2>
          <p><strong>Status:</strong> {requestStatus.status}</p>
          <p><strong>Received Devices:</strong> {requestStatus.received_device_count} / {requestStatus.expected_device_count}</p>

          <h3>Device Status</h3>
          {requestStatus.device_statuses.map((item) => (
            <div key={item.device_id}>
              {item.device_id}: {item.status}
            </div>
          ))}
        </section>
      )}

      {result && (
        <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 10, marginTop: 24 }}>
          <h2>Final Result</h2>
          <p><strong>Object ID:</strong> {result.object_id}</p>
          <p><strong>Final Prediction:</strong> {result.final_prediction}</p>
          <p><strong>Final Method:</strong> {result.final_method}</p>
          <p><strong>Time:</strong> {result.created_at || "-"}</p>

          <hr />

          <h3>ML Output</h3>
          <p><strong>Predicted Location:</strong> {result.ml_result?.predicted_location ?? "-"}</p>
          <p><strong>Confidence:</strong> {result.ml_result?.confidence ?? "-"}</p>

          {result.ml_result?.top_k?.length ? (
            <>
              <h4>ML Top K</h4>
              {result.ml_result.top_k.map((item, idx) => (
                <div key={idx}>
                  #{idx + 1} {item.location} - {item.score}
                </div>
              ))}
            </>
          ) : null}

          <hr />

          <h3>Similarity / KNN Output</h3>
          <p><strong>Predicted Location:</strong> {result.knn_result?.predicted_location ?? "-"}</p>
          <p><strong>K:</strong> {result.knn_result?.k ?? "-"}</p>

          {result.knn_result?.top_matches?.length ? (
            <>
              <h4>Top Matches</h4>
              {result.knn_result.top_matches.map((m, idx) => (
                <div key={idx}>
                  #{idx + 1} | Location: {m.location} | Sequence: {m.sequence_number} | Similarity: {m.similarity_score} | Common MACs: {m.common_mac_count}
                </div>
              ))}
            </>
          ) : null}
        </section>
      )}
    </main>
  );
}