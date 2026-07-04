<script lang="ts">
  import type { GameResponse } from "../lib/api/types";
  import GameCard from "../lib/components/GameCard.svelte";
  import { viewMode, searchQuery, currentSort, currentCategory } from "../lib/stores/ui";

  let { games, loading, onrefresh }: {
    games: GameResponse[];
    loading: boolean;
    onrefresh: () => void;
  } = $props();

  let showAddModal = $state(false);

  const modes: Array<"list" | "blocks" | "banners"> = ["list", "blocks", "banners"];

  function filtered(): GameResponse[] {
    let result = games;
    const q = $searchQuery.toLowerCase();
    if (q) {
      result = result.filter((g) => g.title.toLowerCase().includes(q));
    }
    const cat = $currentCategory;
    if (cat && cat !== "all") {
      if (cat === "_uncategorized") {
        result = result.filter((g) => !g.category || g.category.length === 0);
      } else {
        result = result.filter((g) => g.category?.includes(cat));
      }
    }
    return result;
  }
</script>

<div class="flex h-full">
  <!-- Sidebar -->
  <aside class="w-56 bg-surface-900 border-r border-surface-800 p-3 flex flex-col gap-3 shrink-0">
    <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Categories</h2>
    <button
      class="text-left px-2 py-1 rounded text-sm {$currentCategory === 'all' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-surface-800'}"
      onclick={() => ($currentCategory = "all")}
    >
      All
    </button>
    <button
      class="text-left px-2 py-1 rounded text-sm {$currentCategory === '_uncategorized' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-surface-800'}"
      onclick={() => ($currentCategory = "_uncategorized")}
    >
      Uncategorized
    </button>

    <div class="mt-2 flex flex-col gap-1">
      {#each [...new Set(games.flatMap((g) => g.category ?? []))].sort() as cat}
        <button
          class="text-left px-2 py-1 rounded text-sm {$currentCategory === cat ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-surface-800'}"
          onclick={() => ($currentCategory = cat)}
        >
          {cat}
        </button>
      {/each}
    </div>
  </aside>

  <!-- Main area -->
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center gap-3 px-4 py-2 border-b border-surface-800 bg-surface-900">
      <button class="px-3 py-1 rounded bg-green-700 hover:bg-green-600 text-white text-sm" onclick={() => (showAddModal = true)}>
        + Add Game
      </button>

      <input
        type="text"
        placeholder="Search..."
        bind:value={$searchQuery}
        class="flex-1 max-w-xs px-3 py-1 rounded bg-surface-800 border border-surface-700 text-white text-sm placeholder-gray-500"
      />

      <select
        class="px-2 py-1 rounded bg-surface-800 border border-surface-700 text-white text-sm"
        bind:value={$currentSort}
      >
        <option value="alpha">Alphabetical</option>
        <option value="playtime">Playtime</option>
        <option value="lastplayed">Last played</option>
        <option value="custom">Custom</option>
      </select>

      <div class="flex gap-1">
        {#each modes as mode}
          <button
            class="px-2 py-1 rounded text-xs {$viewMode === mode ? 'bg-blue-600 text-white' : 'bg-surface-800 text-gray-400 hover:bg-surface-700'}"
            onclick={() => ($viewMode = mode)}
          >
            {mode}
          </button>
        {/each}
      </div>
    </div>

    <!-- Game grid -->
    <div class="flex-1 overflow-y-auto p-4">
      {#if loading}
        <div class="flex items-center justify-center h-full text-gray-400">Loading...</div>
      {:else if filtered().length === 0}
        <div class="flex items-center justify-center h-full text-gray-500">
          No games found. Click "Add Game" to get started.
        </div>
      {:else}
        <div
          class="grid gap-3"
          class:grid-cols-1={$viewMode === "list"}
          class:grid-cols-4={$viewMode === "blocks"}
          class:grid-cols-5={$viewMode === "banners"}
        >
          {#each filtered() as game (game.gameid)}
            <GameCard {game} mode={$viewMode} onrefresh />
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
