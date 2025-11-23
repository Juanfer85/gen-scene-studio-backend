import { useState, useEffect, useCallback, useRef } from 'react';

interface UsePollingOptions {
  interval?: number;
  immediate?: boolean;
  timeout?: number;
  onStop?: () => void;
  onError?: (error: Error) => void;
}

interface UsePollingReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  start: () => void;
  stop: () => void;
  restart: () => void;
}

export function usePolling<T>(
  pollFunction: () => Promise<T>,
  dependencies: any[] = [],
  options: UsePollingOptions = {}
): UsePollingReturn<T> {
  const {
    interval = 2000,
    immediate = true,
    timeout = 300000, // 5 minutes
    onStop,
    onError
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);

  const poll = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await pollFunction();
      setData(result);
      setLoading(false);
    } catch (err) {
      setError(err as Error);
      setLoading(false);
      onError?.(err as Error);
    }
  }, [pollFunction, onError]);

  const start = useCallback(() => {
    if (isPolling) return;

    setIsPolling(true);
    startTimeRef.current = Date.now();

    // Set timeout
    if (timeout > 0) {
      timeoutRef.current = setTimeout(() => {
        stop();
        setError(new Error(`Polling timeout after ${timeout}ms`));
      }, timeout);
    }

    // Start polling
    if (immediate) {
      poll();
    }

    intervalRef.current = setInterval(() => {
      // Check if we've exceeded timeout
      if (startTimeRef.current && Date.now() - startTimeRef.current > timeout) {
        stop();
        return;
      }
      poll();
    }, interval);
  }, [isPolling, immediate, interval, timeout, poll]);

  const stop = useCallback(() => {
    setIsPolling(false);

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    startTimeRef.current = null;
    setLoading(false);
    onStop?.();
  }, [onStop]);

  const restart = useCallback(() => {
    stop();
    start();
  }, [stop, start]);

  // Auto-restart when dependencies change
  useEffect(() => {
    if (isPolling) {
      restart();
    }
  }, dependencies);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    data,
    loading,
    error,
    start,
    stop,
    restart
  };
}