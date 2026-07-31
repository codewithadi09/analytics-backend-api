import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/api/client";

interface UseApiDataResult<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Runs `fetcher` whenever `deps` change, tracking loading/error/data.
 * Guards against a slow, stale request overwriting a newer one (e.g.
 * the user changes the date range twice in quick succession) by
 * ignoring any response that isn't from the most recent call.
 */
export function useApiData<T>(fetcher: () => Promise<T>, deps: unknown[]): UseApiDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  const load = useCallback(() => {
    const thisRequestId = ++requestId.current;
    setIsLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        if (requestId.current === thisRequestId) {
          setData(result);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (requestId.current === thisRequestId) {
          setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
          setIsLoading(false);
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    load();
  }, [load]);

  return { data, isLoading, error, refetch: load };
}
