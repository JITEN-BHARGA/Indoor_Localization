import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="main">
      <div className="header">
        <div>
          <h1>IoT Indoor Localization System</h1>
          <p className="small">
            ESP32 + MQTT + FastAPI + PostgreSQL + Next.js dashboard
          </p>
        </div>
        <Link href="/dashboard" className="btn">Open Dashboard</Link>
      </div>

      <div className="grid" style={{ marginTop: 24 }}>
        <section className="card">
          <h3>What this project does</h3>
          <p className="small">
            It predicts the indoor location of an object using Wi-Fi RSSI fingerprints.
            The ESP32 scans nearby access points, the backend compares the scan with
            a trained model and saved fingerprints, and the dashboard shows the result.
          </p>
        </section>
        <section className="card">
          <h3>Prediction pipeline</h3>
          <p className="small">
            Scan payload → ingest API → feature vector → ML prediction → cosine fallback
            if confidence is low → save to database → show on dashboard.
          </p>
        </section>
        <section className="card">
          <h3>Deployment target</h3>
          <p className="small">
            Designed for GitHub + Vercel, with Postgres hosted on Supabase or Neon.
          </p>
        </section>
      </div>
    </main>
  );
}
