// src/App.jsx
import { useState } from 'react';
import GoogleLogin from './GoogleLogin';
import { fetchStepCount } from './api/googleFit';

function App() {
  const [token, setToken] = useState(null);
  const [steps, setSteps] = useState(null);
  const [statusMsg, setStatusMsg] = useState("");

  const onLogin = async (accessToken) => {
    try {
      setToken(accessToken);
      setStatusMsg("Fetching steps from Google Fit...");
      const now = Date.now();
      const oneDayAgo = now - 24 * 60 * 60 * 1000;
      const data = await fetchStepCount(accessToken, oneDayAgo, now);

      if (!data || !data.bucket) {
        setStatusMsg("No step data found.");
        setSteps(0);
        return;
      }

      const stepData =
        data.bucket?.[0]?.dataset?.[0]?.point?.[0]?.value?.[0]?.intVal ?? 0;
      setSteps(stepData);
      setStatusMsg(`Steps fetched: ${stepData}. Sending to encryption pipeline...`);

      // ✅ Send steps to sender.py
      const response = await fetch('http://localhost:5000/send_steps', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ steps: stepData }),
                       });


      if (response.ok) {
        setStatusMsg(`✅ Steps sent to sender.py for encryption.`);
      } else {
        setStatusMsg(`⚠️ Failed to send steps. Server response: ${response.status}`);
      }
    } catch (err) {
      console.error("Error in onLogin:", err);
      setStatusMsg(`❌ Error: ${err.message}`);
    }
  };

  return (
    <div className="container">
      <h1>Google Fit Dashboard</h1>
      {!token ? (
        <GoogleLogin onLogin={onLogin} />
      ) : (
        <div>
          <h2>Steps in last 24 hours</h2>
          <p className="step-count">{steps}</p>
          <p>{statusMsg}</p>
        </div>
      )}
    </div>
  );
}

export default App;
