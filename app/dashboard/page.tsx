"use client";

import { useEffect, useState } from "react";

type LatestData = {
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
  const [data, setData] = useState<LatestData | null>(null);
  const [error, setError] = useState("");

  async function loadLatest() {
    try {
      const res = await fetch("http://127.0.0.1:8000/latest", {
        cache: "no-store",
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const json = await res.json();
      setData(json);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to fetch");
    }
  }

  useEffect(() => {
    loadLatest();
    const id = setInterval(loadLatest, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <main style={{ padding: 24 }}>
      <h1>Indoor Localization Dashboard</h1>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {data && (
        <>
          <h2>Final Result</h2>
          <p><b>Object ID:</b> {data.object_id}</p>
          <p><b>Final Prediction:</b> {data.final_prediction}</p>
          <p><b>Final Method:</b> {data.final_method}</p>
          <p><b>Time:</b> {data.created_at || "-"}</p>

          <hr />

          <h2>ML Output</h2>
          <p><b>Predicted Location:</b> {data.ml_result?.predicted_location ?? "-"}</p>
          <p><b>Confidence:</b> {data.ml_result?.confidence ?? "-"}</p>

          <hr />

          <h2>KNN / Similarity Output</h2>
          <p><b>Predicted Location:</b> {data.knn_result?.predicted_location ?? "-"}</p>
          <p><b>K:</b> {data.knn_result?.k ?? "-"}</p>

          <h3>Top K Matches</h3>
          {data.knn_result?.top_matches?.map((m, idx) => (
            <div key={idx}>
              <p>
                #{idx + 1} | Location: {m.location} | Sequence: {m.sequence_number} | Similarity: {m.similarity_score} | Common MACs: {m.common_mac_count}
              </p>
            </div>
          ))}
        </>
      )}
    </main>
  );
}