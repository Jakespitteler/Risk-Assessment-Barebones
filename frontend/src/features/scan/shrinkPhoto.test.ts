import { afterEach, expect, it, vi } from "vitest";
import { LONGEST_SIDE, shrinkPhoto } from "./shrinkPhoto";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

it("sends the photo as it is when the browser can't draw it", async () => {
  vi.stubGlobal("createImageBitmap", undefined);
  const photo = new Blob(["photo"], { type: "image/png" });
  expect(await shrinkPhoto(photo)).toBe(photo);
});

it("draws a big photo at most 2576 px on its long side, as a JPEG", async () => {
  vi.stubGlobal(
    "createImageBitmap",
    vi.fn(() => Promise.resolve({ width: 8000, height: 6000, close: vi.fn() })),
  );
  const drawImage = vi.fn();
  const jpeg = new Blob(["small"], { type: "image/jpeg" });
  let size = { width: 0, height: 0 };
  vi.spyOn(document, "createElement").mockImplementation(() => {
    const canvas = {
      width: 0,
      height: 0,
      getContext: () => ({ drawImage }),
      toBlob: (done: (blob: Blob) => void, type: string) => {
        size = { width: canvas.width, height: canvas.height };
        expect(type).toBe("image/jpeg");
        done(jpeg);
      },
    };
    return canvas as unknown as HTMLElement;
  });
  expect(await shrinkPhoto(new Blob(["big"]))).toBe(jpeg);
  expect(size).toEqual({ width: LONGEST_SIDE, height: 1932 });
  expect(drawImage).toHaveBeenCalledOnce();
});
