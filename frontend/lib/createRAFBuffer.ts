export function createRAFBuffer<T>(onFlush: (items: T[]) => void) {
  let pending: T[] = [];
  let frameId: number | null = null;

  const flushNow = () => {
    if (frameId !== null) {
      cancelAnimationFrame(frameId);
      frameId = null;
    }
    if (pending.length === 0) return;
    const batch = pending;
    pending = [];
    onFlush(batch);
  };

  const push = (item: T) => {
    pending.push(item);
    if (frameId !== null) return;
    frameId = requestAnimationFrame(() => {
      frameId = null;
      if (pending.length === 0) return;
      const batch = pending;
      pending = [];
      onFlush(batch);
    });
  };

  const cancel = () => {
    if (frameId !== null) {
      cancelAnimationFrame(frameId);
      frameId = null;
    }
    pending = [];
  };

  return { push, flushNow, cancel };
}
