export type InvestigationEventName = "plan" | "tool" | "evidence" | "token" | "citation" | "error" | "done";

export interface InvestigationEvent {
  event: InvestigationEventName;
  data: Record<string, unknown>;
  id?: string;
}

export function openInvestigationStream(url: string, onEvent: (event: InvestigationEvent) => void): EventSource {
  const source = new EventSource(url, { withCredentials: true });
  const eventNames: InvestigationEventName[] = ["plan", "tool", "evidence", "token", "citation", "error", "done"];
  eventNames.forEach((eventName) => {
    source.addEventListener(eventName, (event) => {
      const message = event as MessageEvent<string>;
      let data: Record<string, unknown> = {};
      try {
        data = JSON.parse(message.data) as Record<string, unknown>;
      } catch {
        data = { value: message.data };
      }
      onEvent({ event: eventName, data, id: message.lastEventId || undefined });
      if (eventName === "done" || eventName === "error") source.close();
    });
  });
  return source;
}
