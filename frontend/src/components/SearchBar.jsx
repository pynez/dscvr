// frontend/src/components/SearchBar.jsx
import { useState } from "react";

export function SearchBar({ initialQuery, onSubmit, isLoading }) {
  const [localQuery, setLocalQuery] = useState(initialQuery || "");

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit(localQuery);
  }

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <label className="search-label" htmlFor="query">
        Enter a song — artist
      </label>
      <div className="search-row">
        <input
          id="query"
          className="search-input"
          placeholder="e.g. Snooze — SZA"
          value={localQuery}
          onChange={(e) => setLocalQuery(e.target.value)}
        />
        <button
          className="search-button"
          type="submit"
          disabled={isLoading || !localQuery.trim()}
        >
          {isLoading ? "Finding..." : "Recommend"}
        </button>
      </div>
    </form>
  );
}
