import { writable } from "svelte/store";
import type { GameResponse, ConfigResponse } from "../api/types";

export const games = writable<GameResponse[]>([]);
export const config = writable<ConfigResponse>({});
export const viewMode = writable<"list" | "blocks" | "banners">("list");
export const searchQuery = writable("");
export const currentSort = writable("alpha");
export const currentCategory = writable("all");
export const loading = writable(true);
