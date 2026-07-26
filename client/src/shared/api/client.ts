import type { InvestigationState } from "@/shared/types/investigation";

export class ApiClientError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiClientError";
  }
}

export interface ApiClientOptions {
  baseUrl?: string;
  token?: string;
}

export class InvestigationApiClient {
  private readonly baseUrl: string;
  private readonly token?: string;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? "/api/v1";
    this.token = options.token;
  }

  async getInvestigation(id: string, signal?: AbortSignal): Promise<InvestigationState> {
    const response = await fetch(`${this.baseUrl}/investigations/${encodeURIComponent(id)}`, {
      headers: this.headers(),
      credentials: "include",
      signal,
    });
    if (!response.ok) {
      throw new ApiClientError(response.status, `Investigation request failed (${response.status})`);
    }
    return response.json() as Promise<InvestigationState>;
  }

  async postResource(id: string, resource: string, payload: unknown): Promise<InvestigationState> {
    const response = await fetch(`${this.baseUrl}/investigations/${encodeURIComponent(id)}/${resource}`, {
      method: "POST",
      headers: { ...this.headers(), "content-type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new ApiClientError(response.status, `Investigation mutation failed (${response.status})`);
    }
    return response.json() as Promise<InvestigationState>;
  }

  private headers(): HeadersInit {
    return this.token ? { authorization: `Bearer ${this.token}` } : {};
  }
}
