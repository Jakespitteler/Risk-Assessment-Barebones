/** The longest side Claude reads at full detail; anything bigger is only slower to send. */
export const LONGEST_SIDE = 2576;
const JPEG_QUALITY = 0.85;

/**
 * Make a photo at most `LONGEST_SIDE` pixels on its long edge, as a JPEG, so a big phone
 * photo is quick to send on a site's signal and under the back end's 7 MB limit (task
 * 0033). A browser that can't draw it, or runs out of room, sends the photo as it is.
 */
export async function shrinkPhoto(photo: Blob): Promise<Blob> {
  if (typeof createImageBitmap !== "function") return photo;
  try {
    const image = await createImageBitmap(photo);
    const scale = Math.min(
      1,
      LONGEST_SIDE / Math.max(image.width, image.height),
    );
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(image.width * scale);
    canvas.height = Math.round(image.height * scale);
    const context = canvas.getContext("2d");
    if (!context) return photo;
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    image.close();
    const shrunk = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", JPEG_QUALITY);
    });
    // Let the browser have the canvas's memory back before the next photo.
    canvas.width = 0;
    canvas.height = 0;
    return shrunk ?? photo;
  } catch {
    return photo;
  }
}
