/**
 * Pure helper to calculate the next 00:00:00 UTC boundary after lastResetAt.
 * @param {Date|string|number|null} lastResetAt - Timestamp of last reset
 * @returns {Date} Date object for next midnight UTC
 */
export function getNextResetUTC(lastResetAt) {
  const baseDate = lastResetAt ? new Date(lastResetAt) : new Date();
  const validDate = isNaN(baseDate.getTime()) ? new Date() : baseDate;

  // Next UTC day at 00:00:00.000Z
  const nextReset = new Date(Date.UTC(
    validDate.getUTCFullYear(),
    validDate.getUTCMonth(),
    validDate.getUTCDate() + 1,
    0, 0, 0, 0
  ));

  return nextReset;
}

/**
 * Pure helper to compute live countdown from nextResetUTC and now.
 * @param {Date|string} nextResetUTC - Target reset time
 * @param {Date} [now] - Current time (defaults to new Date())
 * @returns {{h: number, m: number, s: number}}
 */
export function getCountdown(nextResetUTC, now = new Date()) {
  const target = nextResetUTC ? new Date(nextResetUTC) : getNextResetUTC(now);
  const targetMs = isNaN(target.getTime()) ? getNextResetUTC(now).getTime() : target.getTime();
  const currentMs = now ? now.getTime() : Date.now();

  const diffMs = Math.max(0, targetMs - currentMs);

  const h = Math.floor(diffMs / (1000 * 60 * 60));
  const m = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  const s = Math.floor((diffMs % (1000 * 60)) / 1000);

  return { h, m, s };
}

/**
 * Formats countdown object into string "Resetting in Xh Ym Zs (UTC)".
 * @param {Date|string} nextResetUTC 
 * @param {Date} [now] 
 * @returns {string}
 */
export function formatCountdown(nextResetUTC, now = new Date()) {
  const { h, m, s } = getCountdown(nextResetUTC, now);
  return `Resetting in ${h}h ${m}m ${s}s (UTC)`;
}
