import React from 'react';
import ReactDOM from 'react-dom/client';

const App: React.FC = () => {
  return (
    <main>
      <h1>Audio-Visual Script Repository</h1>
      <p>
        Welcome to the Spiral Bloom editor. Frontend scaffolding is ready; begin wiring up the
        narrative editor and playback UI here.
      </p>
    </main>
  );
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
