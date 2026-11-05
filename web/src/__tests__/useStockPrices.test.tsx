import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useStockPrices } from "@/lib/useStockPrices";

function pendingResponse() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((done) => { resolve = done; });
  return { promise, resolve };
}

const quote = { price: 12, change: 1, prevClose: 11 };

describe("useStockPrices polling", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("does not overlap refreshes when one request takes several intervals", async () => {
    const first = pendingResponse();
    fetchMock.mockReturnValue(first.promise);
    const { result } = renderHook(() => useStockPrices(["SLOW"]));

    await act(async () => { await vi.advanceTimersByTimeAsync(90_000); });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(result.current.loading).toBe(true);

    await act(async () => { first.resolve(Response.json({ SLOW: quote })); });
    expect(result.current.data.SLOW).toEqual(quote);
    expect(result.current.loading).toBe(false);
    fetchMock.mockReturnValue(new Promise<Response>(() => {}));
    await act(async () => { await vi.advanceTimersByTimeAsync(29_999); });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("shows completed batches without waiting for the full universe", async () => {
    const later = pendingResponse();
    fetchMock.mockResolvedValueOnce(Response.json({ PART00: quote }));
    fetchMock.mockReturnValueOnce(later.promise);
    const symbols = Array.from({ length: 31 }, (_, i) => `PART${String(i).padStart(2, "0")}`);
    const { result } = renderHook(() => useStockPrices(symbols));

    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    expect(result.current.data.PART00).toEqual(quote);
    expect(result.current.loading).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[0][0]).split("symbols=")[1].split(",")).toHaveLength(30);
    await act(async () => { await vi.advanceTimersByTimeAsync(60_000); });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    await act(async () => { later.resolve(Response.json({ PART30: quote })); });
    expect(result.current.data.PART30).toEqual(quote);
    expect(result.current.loading).toBe(false);
  });

  it("aborts obsolete requests and ignores their late results after symbols change", async () => {
    const obsolete = pendingResponse();
    const latest = pendingResponse();
    fetchMock.mockReturnValueOnce(obsolete.promise).mockReturnValueOnce(latest.promise);
    const { result, rerender } = renderHook(
      ({ symbols }) => useStockPrices(symbols), { initialProps: { symbols: ["OLD_QUOTE"] } },
    );
    const oldSignal = fetchMock.mock.calls[0][1]?.signal;
    rerender({ symbols: ["NEW_QUOTE"] });
    expect(oldSignal?.aborted).toBe(true);

    await act(async () => { obsolete.resolve(Response.json({ OLD_QUOTE: quote })); });
    expect(result.current.data.OLD_QUOTE).toBeUndefined();
    await act(async () => { latest.resolve(Response.json({ NEW_QUOTE: quote })); });
    expect(result.current.data.NEW_QUOTE).toEqual(quote);
  });

  it("aborts on unmount without starting subsequent batches or poll cycles", async () => {
    const current = pendingResponse();
    fetchMock.mockReturnValue(current.promise);
    const { unmount } = renderHook(
      () => useStockPrices(Array.from({ length: 61 }, (_, i) => `CANCEL${i}`)),
    );
    const signal = fetchMock.mock.calls[0][1]?.signal;
    unmount();
    expect(signal?.aborted).toBe(true);
    await act(async () => {
      current.resolve(Response.json({}));
      await vi.advanceTimersByTimeAsync(90_000);
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not refetch for a reordered but unchanged symbol set", () => {
    fetchMock.mockReturnValue(new Promise<Response>(() => {}));
    const { rerender } = renderHook(
      ({ symbols }) => useStockPrices(symbols), { initialProps: { symbols: ["ORDER_B", "ORDER_A"] } },
    );
    rerender({ symbols: ["ORDER_A", "ORDER_B"] });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not poll an empty symbol list", async () => {
    const { result } = renderHook(() => useStockPrices([]));
    await act(async () => { await vi.advanceTimersByTimeAsync(90_000); });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it("reports failed HTTP requests and retries only after the refresh delay", async () => {
    const warning = vi.spyOn(console, "warn").mockImplementation(() => {});
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 502 }));
    const { result } = renderHook(() => useStockPrices(["RETRY_QUOTE"]));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect(warning).toHaveBeenCalledWith("Stock price refresh failed:", expect.any(Error));
    expect(result.current.loading).toBe(false);
    fetchMock.mockResolvedValueOnce(Response.json({ RETRY_QUOTE: quote }));
    await act(async () => { await vi.advanceTimersByTimeAsync(30_000); });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(result.current.data.RETRY_QUOTE).toEqual(quote);
  });
});
