<script lang="ts">
  import { Search, LayoutList, LayoutGrid, Columns3, Plus, Gamepad2 } from "lucide-svelte";
  import type { GameResponse } from "../lib/api/types";
  import GameCard from "../lib/components/GameCard.svelte";
  import { toast } from "svelte-sonner";
  import * as api from "../lib/api/client";

  let {
    games,
    loading,
    onrefresh,
    onadd,
    onedit,
    onshowlogs,
  }: {
    games: GameResponse[];
    loading: boolean;
    onrefresh: () => void;
    onadd: () => void;
    onedit: (game: GameResponse) => void;
    onshowlogs: (gameid: string) => void;
  } = $props();

  let viewMode = $state<"list" | "blocks" | "banners">("list");
  let searchQuery = $state("");
  let sortMode = $state("alpha");
  let runningGames = $state<Record<string, number>>({});


  // Poll running games
  $effect(() => {
    const interval = setInterval(async () => {
      try {
        runningGames = await api.getRunningGames();
      } catch {}
    }, 3000);
    return () => clearInterval(interval);
  });

  let filtered = $derived.by(() => {
    let result = games;
    const q = searchQuery.toLowerCase();
    if (q) result = result.filter(g => g.title.toLowerCase().includes(q));

    if (sortMode === "alpha") {
      result = [...result].sort((a, b) => a.title.localeCompare(b.title));
    } else if (sortMode === "playtime") {
      result = [...result].sort((a, b) => (b.playtime || 0) - (a.playtime || 0));
    } else if (sortMode === "lastplayed") {
      result = [...result].sort((a, b) => (b.lastplayed || 0) - (a.lastplayed || 0));
    }
    return result;
  });

  async function handleDelete(game: GameResponse) {
    if (!confirm(`Delete "${game.title}"?`)) return;
    try {
      await api.deleteGame(game.gameid);
      toast.success(`Deleted ${game.title}`);
      onrefresh();
    } catch (e) {
      toast.error("Failed to delete game");
    }
  }

  async function handleDuplicate(game: GameResponse) {
    const title = prompt("New title:", `${game.title} (Copy)`);
    if (!title) return;
    try {
      await api.duplicateGame(game.gameid, title);
      toast.success(`Duplicated as ${title}`);
      onrefresh();
    } catch (e) {
      toast.error("Failed to duplicate");
    }
  }

  async function handleToggleHidden(game: GameResponse) {
    try {
      await api.toggleHidden(game.gameid);
      toast.success(game.hidden ? "Unhidden" : "Hidden");
      onrefresh();
    } catch (e) {
      toast.error("Failed to toggle hidden");
    }
  }

  async function handleSetCategory(game: GameResponse, cat: string) {
    const current = game.category ?? [];
    const updated = current.includes(cat) ? current.filter(c => c !== cat) : [...current, cat];
    try {
      await api.setCategory(game.gameid, updated);
      onrefresh();
    } catch {}
  }
</script>

<div class="flex h-full">
  <!-- Category sidebar removed -->

  <!-- Main area -->
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center gap-3 px-4 py-2.5 border-b border-surface-800 bg-surface-elevated/80 backdrop-blur-md">
      <button class="flex items-center gap-1.5 px-4 py-2 btn-primary text-sm font-medium rounded-lg" onclick={onadd}>
        <Plus size={16} /> Add Game
      </button>

      <div class="relative flex-1 max-w-xs">
        <Search size={16} class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          type="text"
          placeholder="Search games..."
          bind:value={searchQuery}
          class="w-full pl-8 pr-3 py-1.5 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>

      <div class="flex items-center gap-1 bg-surface-card rounded-lg p-0.5 border border-surface-700">
        <button class="px-2.5 py-1.5 rounded-md text-sm transition-all {viewMode === 'list' ? 'bg-surface-hover text-white shadow-sm' : 'text-gray-500 hover:text-white'}" onclick={() => (viewMode = "list")} title="List view"><LayoutList size={16} /></button>
        <button class="px-2.5 py-1.5 rounded-md text-sm transition-all {viewMode === 'blocks' ? 'bg-surface-hover text-white shadow-sm' : 'text-gray-500 hover:text-white'}" onclick={() => (viewMode = "blocks")} title="Blocks view"><LayoutGrid size={16} /></button>
        <button class="px-2.5 py-1.5 rounded-md text-sm transition-all {viewMode === 'banners' ? 'bg-surface-hover text-white shadow-sm' : 'text-gray-500 hover:text-white'}" onclick={() => (viewMode = "banners")} title="Banners view"><Columns3 size={16} /></button>
      </div>

      <select
        class="px-2 py-1.5 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm focus:outline-none focus:border-blue-500"
        bind:value={sortMode}
      >
        <option value="alpha">A-Z</option>
        <option value="playtime">Playtime</option>
        <option value="lastplayed">Last played</option>
      </select>
    </div>

    <!-- Game grid -->
    <div class="flex-1 overflow-y-auto p-4">
      {#if loading}
        <div class="flex items-center justify-center h-full"><div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>
      {:else if filtered.length === 0}
        <div class="flex flex-col items-center justify-center h-full text-gray-500 gap-2">
          <Gamepad2 size={48} class="text-gray-700" />
          <p class="text-lg">No games found</p>
          {#if searchQuery}
            <p class="text-sm">Try changing your search or filters</p>
          {:else}
            <p class="text-sm">Click "Add Game" to get started</p>
          {/if}
        </div>
      {:else}
        <div
          class="grid gap-3"
          class:grid-cols-1={viewMode === "list"}
          class:grid-cols-3={viewMode === "blocks"}
          class:grid-cols-4={viewMode === "banners"}
        >
          {#each filtered as game (game.gameid)}
            <GameCard {game} mode={viewMode} {onrefresh} onedit={(g) => onedit(g)} />
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
