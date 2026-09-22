/** Best-effort partial string value for a JSON key while the model is still streaming. */
export function partialJsonStringField(buffer: string, field: string): string {
  const key = `"${field}"`;
  const idx = buffer.indexOf(key);
  if (idx < 0) return "";

  let i = idx + key.length;
  while (i < buffer.length && buffer[i] !== ":") i += 1;
  i += 1;
  while (i < buffer.length && /\s/.test(buffer[i])) i += 1;
  if (buffer[i] !== '"') return "";
  i += 1;

  let out = "";
  while (i < buffer.length) {
    const ch = buffer[i];
    if (ch === '"') break;
    if (ch === "\\" && i + 1 < buffer.length) {
      const next = buffer[i + 1];
      if (next === "n") out += "\n";
      else if (next === "t") out += "\t";
      else if (next === '"') out += '"';
      else if (next === "\\") out += "\\";
      else out += next;
      i += 2;
      continue;
    }
    out += ch;
    i += 1;
  }
  return out;
}
