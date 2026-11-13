// The attributes that tie a field to its error, so a screen reader reads them together.
export function fieldProps(
  path: string,
  errorFor: (path: string) => string | undefined,
) {
  const error = errorFor(path);
  return {
    id: path,
    "aria-invalid": Boolean(error),
    "aria-describedby": error ? `${path}-error` : undefined,
  };
}
