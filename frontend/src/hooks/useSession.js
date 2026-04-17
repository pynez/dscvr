// frontend/src/hooks/useSession.js
import { useMemo } from "react";

const STORAGE_KEY = "dscvr-user-id";

function generateUUID() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older browsers
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export function useSession() {
  const userId = useMemo(() => {
    try {
      let id = localStorage.getItem(STORAGE_KEY);
      if (!id) {
        id = generateUUID();
        localStorage.setItem(STORAGE_KEY, id);
      }
      return id;
    } catch {
      // localStorage may be unavailable (private mode, etc.)
      return generateUUID();
    }
  }, []);

  return { userId };
}
