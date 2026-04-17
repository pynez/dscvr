// frontend/src/hooks/useInteractions.js
import { useCallback } from "react";
import { useSession } from "./useSession";
import { postInteraction } from "../api/client";

export function useInteractions(feature = null) {
  const { userId } = useSession();

  const track = useCallback(
    (trackId, interactionType, tags = []) => {
      // Fire-and-forget — never block UI
      postInteraction({
        userId,
        trackId: String(trackId),
        interactionType,
        feature,
        tags,
      }).catch(() => {
        // Silently swallow — interactions are best-effort
      });
    },
    [userId, feature]
  );

  return { track, userId };
}
