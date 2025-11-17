const { useState, useEffect } = React;

/**
 * A custom hook to fetch and provide the classical mode UI configuration.
 * @returns {{config: object|null, loading: boolean, error: Error|null}}
 */
function useClassicalConfig() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Instead of fetching, we now read the config from a global variable
  // that is loaded by a script in index.html. This is more robust.
  useEffect(() => {
    let attempts = 0;
    const interval = setInterval(() => {
      if (window.__CLASSICAL_CONFIG__) {
        setConfig(window.__CLASSICAL_CONFIG__);
        setLoading(false);
        clearInterval(interval);
      } else if (attempts > 20) { // Wait for up to 2 seconds
        const err = new Error('Classical mode configuration failed to load. Check classicalConfig.json and network tab.');
        setError(err);
        setLoading(false);
        clearInterval(interval);
      }
      attempts++;
    }, 100);

    return () => {
      clearInterval(interval);
    }
  }, []);

  return { config, loading, error };
}