// src/components/GoogleLogin.jsx
import { useEffect, useRef } from 'react';

function GoogleLogin({ onLogin }) {
  const tokenClientRef = useRef(null);

  useEffect(() => {
    if (window.google) {
      tokenClientRef.current = window.google.accounts.oauth2.initTokenClient({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        scope:
          'https://www.googleapis.com/auth/fitness.activity.read ' +
          'https://www.googleapis.com/auth/fitness.body.read ' +
          'https://www.googleapis.com/auth/fitness.sleep.read',
        callback: (tokenResponse) => {
          console.log('✅ Access Token:', tokenResponse.access_token);
          onLogin(tokenResponse.access_token);
        },
      });
    }
  }, []);

  const handleLogin = () => {
    if (tokenClientRef.current) {
      tokenClientRef.current.requestAccessToken();
    }
  };

  return (
    <div>
      <button onClick={handleLogin}>Sign in with Google Fit</button>
    </div>
  );
}

export default GoogleLogin;
