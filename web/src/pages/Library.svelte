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
  let categoryFilter = $state("all");
  let runningGames = $state<Record<string, number>>({});
  let categories = $state<string[]>([]);

  $effect(() => {
    // Derive categories from games
    const catSet = new Set<string>();
    games.forEach(g => (g.category ?? []).forEach(c => catSet.add(c)));
    categories = [...catSet].sort();
  });

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
    if (categoryFilter && categoryFilter !== "all") {
      if (categoryFilter === "_uncategorized") {
        result = result.filter(g => !g.category || g.category.length === 0);
      } else {
        result = result.filter(g => g.category?.includes(categoryFilter));
      }
    }
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
  <!-- Category sidebar -->
  <aside class="w-48 bg-surface-900 border-r border-surface-800 p-3 flex flex-col gap-1 shrink-0 overflow-y-auto">
    <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">Categories</h3>
    <button
      class="text-left px-2 py-1.5 rounded text-sm transition-colors {categoryFilter === 'all' ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:text-white hover:bg-surface-800'}"
      onclick={() => (categoryFilter = "all")}
    >All <span class="text-gray-600 text-xs ml-1">({games.length})</span></button>
    <button
      class="text-left px-2 py-1.5 rounded text-sm transition-colors {categoryFilter === '_uncategorized' ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:text-white hover:bg-surface-800'}"
      onclick={() => (categoryFilter = "_uncategorized")}
    >Uncategorized</button>
    {#each categories as cat}
      <button
        class="text-left px-2 py-1.5 rounded text-sm transition-colors {categoryFilter === cat ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:text-white hover:bg-surface-800'}"
        onclick={() => (categoryFilter = cat)}
      >{cat}</button>
    {/each}
  </aside>

  <!-- Main area -->
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center gap-3 px-4 py-2.5 border-b border-surface-800 bg-surface-900/50 backdrop-blur">
      <button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors" onclick={onadd}>
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

      <div class="flex items-center gap-1 bg-surface-800 rounded-lg p-0.5">
        <button class="px-2.5 py-1.5 rounded-md text-sm transition-colors {viewMode === 'list' ? 'bg-surface-700 text-white' : 'text-gray-400 hover:text-white'}" onclick={() => (viewMode = "list")} title="List view"><LayoutList size={16} /></button>
        <button class="px-2.5 py-1.5 rounded-md text-sm transition-colors {viewMode === 'blocks' ? 'bg-surface-700 text-white' : 'text-gray-400 hover:text-white'}" onclick={() => (viewMode = "blocks")} title="Blocks view"><LayoutGrid size={16} /></button>
        <button class="px-2.5 py-1.5 rounded-md text-sm transition-colors {viewMode === 'banners' ? 'bg-surface-700 text-white' : 'text-gray-400 hover:text-white'}" onclick={() => (viewMode = "banners")} title="Banners view"><Columns3 size={16} /></button>
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
        <div class="flex items-center justify-center h-full"><div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" /></div>
      {:else if filtered.length === 0}
        <div class="flex flex-col items-center justify-center h-full text-gray-500 gap-2">
          <Gamepad2 size={48} class="text-gray-700" />
          <p class="text-lg">No games found</p>
          {#if searchQuery || categoryFilter !== "all"}
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
            <GameCard
              {game}
              mode={viewMode}
              isRunning={game.gameid in runningGames}
              onplay={async () => {
                if (game.gameid in runningGames) {
                  await api.killGame(game.gameid);
                  toast.success("Game stopped");
                } else {
                  await api.launchGame(game.gameid);
                  toast.success("Launching...");
                }
                onrefresh();
              }}
              oncontext={(e) => openContext(game, e)}
            />
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
