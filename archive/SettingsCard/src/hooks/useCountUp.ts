import { useEffect, useRef, useState } from "react";

interface UseCountUpOptions {
  duration?: number;
  format?: (value: number) => number;
}

export function useCountUp(target: number, { duration = 800, format }: UseCountUpOptions = {}) {
  const startTimestamp = useRef<number | null>(null);
  const [value, setValue] = useState(0);

  useEffect(() => {
    let rafId: number;

    const startValue = value;
    const delta = target - startValue;

    const step: FrameRequestCallback = (timestamp) => {
      if (startTimestamp.current === null) {
        startTimestamp.current = timestamp;
      }
      const progress = Math.min((timestamp - startTimestamp.current) / duration, 1);
      let nextValue = startValue + delta * progress;
      if (format) {
        nextValue = format(nextValue);
      }
      setValue(nextValue);
      if (progress < 1) {
        rafId = requestAnimationFrame(step);
      }
    };

    rafId = requestAnimationFrame(step);

    return () => {
      startTimestamp.current = null;
      cancelAnimationFrame(rafId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, duration]);

  return value;
}
