export type SseEvent = { event: string; data: string };

/** `\n\n` 단위로 SSE 블록을 분리하고, 불완전한 꼬리는 remainder로 반환 */
export function consumeSseBuffer(buffer: string): {
  remainder: string;
  events: SseEvent[];
} {
  const events: SseEvent[] = [];
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";
  for (const block of parts) {
    if (!block.trim()) continue;
    let ev = "message";
    let data = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) ev = line.slice(6).trim();
      else if (line.startsWith("data:")) data = line.slice(5).trimStart();
    }
    if (data) events.push({ event: ev, data });
  }
  return { remainder, events };
}
