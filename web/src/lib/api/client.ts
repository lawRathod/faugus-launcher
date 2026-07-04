/**
 * API client for the Faugus Launcher backend.
 *
 * All calls go through `/api/*` which is proxied to `localhost:9876`
 * during development, or directly served by the Tauri sidecar in production.
 */

const BASE = ""; // Same origin — Vite proxy or Tauri sidecar

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE}${path}`;
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.text().catch(() => "");
    throw new Error(`HTTP ${resp.status} ${resp.statusText}: ${body}`);
  }
  return resp.json();
}

function formRequest<T>(path: string, formData: FormData): Promise<T> {
  return fetch(`${BASE}${path}`, { method: "POST", body: formData }).then(
    (r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    }
  );
}

// ── Games ───────────────────────────────────────────────────────────

import type {
  GameResponse,
  GameCreate,
  DirEntry,
  GameLogs,
  SystemStatus,
  ConfigResponse,
  SteamStatus,
  SteamGame,
  RunnerInfo,
  RunnerVariant,
} from "./types";

export async function listGames(params?: {
  search?: string;
  sort?: string;
  category?: string;
  hidden?: boolean;
}): Promise<GameResponse[]> {
  const q = new URLSearchParams();
  if (params?.search) q.set("search", params.search);
  if (params?.sort) q.set("sort", params.sort);
  if (params?.category) q.set("category", params.category);
  if (params?.hidden) q.set("hidden", "1");
  return request(`/api/games?${q}`);
}

export async function getGame(gameid: string): Promise<GameResponse> {
  return request(`/api/games/${gameid}`);
}

export async function createGame(data: GameCreate): Promise<GameResponse> {
  return request("/api/games", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateGame(
  gameid: string,
  data: GameCreate
): Promise<GameResponse> {
  return request(`/api/games/${gameid}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteGame(gameid: string): Promise<void> {
  await fetch(`${BASE}/api/games/${gameid}`, { method: "DELETE" });
}

export async function launchGame(gameid: string): Promise<{
  process_id: number;
  status: string;
}> {
  return request(`/api/games/${gameid}/launch`, { method: "POST" });
}

export async function killGame(gameid: string): Promise<void> {
  await fetch(`${BASE}/api/games/${gameid}/kill`, { method: "POST" });
}

export async function duplicateGame(
  gameid: string,
  title: string
): Promise<GameResponse> {
  return request(`/api/games/${gameid}/duplicate`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function toggleHidden(gameid: string): Promise<GameResponse> {
  return request(`/api/games/${gameid}/hide`, { method: "PATCH" });
}

export async function setCategory(
  gameid: string,
  categories: string[]
): Promise<GameResponse> {
  return request(`/api/games/${gameid}/category`, {
    method: "PATCH",
    body: JSON.stringify({ categories }),
  });
}

export async function getRunningGames(): Promise<Record<string, number>> {
  return request("/api/games/status");
}

// ── Config ──────────────────────────────────────────────────────────

export async function getConfig(): Promise<ConfigResponse> {
  return request("/api/config");
}

export async function updateConfig(
  data: Record<string, string>
): Promise<ConfigResponse> {
  return request("/api/config", {
    method: "PUT",
    body: JSON.stringify({ key_values: data }),
  });
}

// ── Steam ───────────────────────────────────────────────────────────

export async function getSteamStatus(): Promise<SteamStatus> {
  return request("/api/steam/status");
}

export async function listSteamGames(): Promise<SteamGame[]> {
  return request("/api/steam/games");
}

// ── Runners ─────────────────────────────────────────────────────────

export async function listRunners(): Promise<RunnerInfo[]> {
  return request("/api/runners");
}

export async function getLatestRunnerVersions(): Promise<RunnerVariant[]> {
  return request("/api/runners/latest");
}

// ── Files ───────────────────────────────────────────────────────────

export async function browseDirectory(
  path: string
): Promise<DirEntry[]> {
  return request(`/api/files/browse?path=${encodeURIComponent(path)}`);
}

export async function uploadIcon(
  gameid: string,
  file: File
): Promise<{ path: string }> {
  const fd = new FormData();
  fd.append("gameid", gameid);
  fd.append("file", file);
  return formRequest("/api/files/icon", fd);
}

export async function uploadBanner(
  gameid: string,
  file: File
): Promise<{ path: string }> {
  const fd = new FormData();
  fd.append("gameid", gameid);
  fd.append("file", file);
  return formRequest("/api/files/banner", fd);
}

export async function suggestPrefix(
  title: string
): Promise<{ prefix: string }> {
  return request(
    `/api/files/prefix-suggest?title=${encodeURIComponent(title)}`
  );
}

// ── Logs ────────────────────────────────────────────────────────────

export async function getGameLogs(gameid: string): Promise<GameLogs> {
  return request(`/api/logs/${gameid}`);
}

// ── System ──────────────────────────────────────────────────────────

export async function getSystemStatus(): Promise<SystemStatus> {
  return request("/api/system/status");
}

// ── Env ─────────────────────────────────────────────────────────────

export async function getEnvar(): Promise<string[]> {
  return request("/api/envar");
}

export async function setEnvar(vars: string[]): Promise<string[]> {
  return request("/api/envar", {
    method: "PUT",
    body: JSON.stringify(vars),
  });
}
