// frontend/src/App.jsx
import "./styles/globals.css";
import { Layout } from "./components/Layout";
import { SearchBar } from "./components/SearchBar";
import { TrackCard } from "./components/TrackCard";
import { useRecommendations } from "./hooks/useRecommendations";

function App() {
  const {
    query,
    setQuery,
    submit,
    matchedTrack,
    recommendations,
    isLoading,
    error,
  } = useRecommendations();

  return (
    <Layout>
      <SearchBar
        initialQuery={query}
        onSubmit={submit}
        isLoading={isLoading}
      />

      {error && <p className="error-text">{error}</p>}

      {matchedTrack && (
        <section className="matched-section">
          <h2>You asked for:</h2>
          <p className="matched-track">
            <strong>{matchedTrack.title}</strong> — {matchedTrack.artist}
          </p>
        </section>
      )}

      <section className="results-section">
        {isLoading && <p className="dim-text">Crunching vibes…</p>}

        {!isLoading && !recommendations.length && !error && (
          <p className="dim-text">
            Try searching for a track to see recommendations.
          </p>
        )}

        <div className="results-grid">
          {recommendations.map((track) => (
            <TrackCard key={`${track.row_index}-${track.name}`} track={track} />
          ))}
        </div>
      </section>
    </Layout>
  );
}

export default App;
