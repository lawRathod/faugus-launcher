// ── API response types (mirror Pydantic models in faugus/api/models.py) ──

export interface GameResponse {
  gameid: string;
  title: string;
  path: string;
  prefix: string;
  launch_arguments: string;
  game_arguments: string;
  runner: string;
  protonfix: string;
  icon: string;
  banner: string;
  category: string[];
  hidden: boolean;
  mangohud: boolean | string;
  gamemode: boolean | string;
  disable_hidraw: boolean | string;
  prevent_sleep: boolean;
  playtime: number;
  lastplayed: number;
  addapp_checkbox: boolean | string;
  addapp: string;
  addapp_bat: string;
  addapp_delay: string;
  addapp_first: string;
  lossless_enabled: boolean | string;
  lossless_multiplier: string;
  lossless_flow: string;
  lossless_performance: string;
  lossless_hdr: string;
  lossless_present: string;
  settings: Record<string, unknown>;
}

export interface GameCreate {
  title: string;
  path: string;
  prefix: string;
  launch_arguments?: string;
  game_arguments?: string;
  runner?: string;
  protonfix?: string;
  icon?: string;
  banner?: string;
  category?: string[];
  hidden?: boolean;
  mangohud?: boolean;
  gamemode?: boolean;
  disable_hidraw?: boolean;
  prevent_sleep?: boolean;
}

export interface ConfigResponse {
  [key: string]: string;
}

export interface SteamStatus {
  version: "native" | "flatpak" | null;
  steam_id: string | null;
  shortcuts_path: string | null;
}

export interface SteamGame {
  appid: string;
  name: string;
  icon: string;
}

export interface RunnerInfo {
  name: string;
  path: string;
  type: string;
  is_latest: boolean;
}

export interface RunnerVariant {
  key: string;
  display_name: string;
  latest_version: string | null;
}

export interface DirEntry {
  name: string;
  path: string;
  type: "file" | "dir";
  size: number;
}

export interface GameLogs {
  gameid: string;
  proton_log: string;
  umu_log: string;
}

export interface SystemStatus {
  version: string;
  running_games: Record<string, number>;
}

export enum GameState {
  Stopped = "stopped",
  Launching = "launching",
  Running = "running",
}
