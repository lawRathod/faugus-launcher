<script lang="ts">
  import type { GameResponse } from "../api/types";
  import { deleteGame, launchGame, killGame, getRunningGames } from "../api/client";

  let { game, mode, onrefresh }: {
    game: GameResponse;
    mode: "list" | "blocks" | "banners";
    onrefresh: () => void;
  } = $props();

  let running = $state(false);
  let contextOpen = $state(false);

  $effect(() => {
    // Check if game is running
    getRunningGames().then((r) => {
      running = game.gameid in r;
    });
    const interval = setInterval(async () => {
      const r = await getRunningGames();
      running = game.gameid in r;
    }, 3000);
    return () => clearInterval(interval);
  });

  async function handlePlay() {
    try {
      if (running) {
        await killGame(game.gameid);
        running = false;
      } else {
        await launchGame(game.gameid);
        running = true;
      }
    } catch (e) {
      console.error("Failed:", e);
    }
  }

  async function handleDelete() {
    if (confirm(`Delete "${game.title}"?`)) {
      await deleteGame(game.gameid);
      onrefresh();
    }
  }

  function formatPlaytime(seconds: number): string {
    if (!seconds) return "";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h === 0) return `${m}m`;
    if (m === 0) return `${h}h`;
    return `${h}h ${m}m`;
  }

  // Default icon — use $state to track reactivity
  let iconUrl = $derived(game.icon || "/favicon.svg");

  function closeContext() {
    contextOpen = false;
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
  class="relative group cursor-pointer rounded-lg border border-surface-800 hover:border-blue-600 transition-colors"
  class:bg-surface-900={mode !== "banners"}
  class:bg-surface-950={mode === "banners"}
  onclick={() => contextOpen = !contextOpen}
  onmouseleave={closeContext}
  role="button"
  tabindex="0"
>
  {#if mode === "list"}
    <div class="flex items-center gap-3 p-2">
      <img src={iconUrl} alt="" class="w-10 h-10 rounded object-cover" />
      <div class="flex-1 min-w-0">
        <div class="text-sm font-medium truncate">{game.title}</div>
        {#if formatPlaytime(game.playtime)}
          <div class="text-xs text-gray-400">{formatPlaytime(game.playtime)}</div>
        {/if}
      </div>
      <button
        class="px-3 py-1 rounded text-xs font-medium {running ? 'bg-red-700 hover:bg-red-600' : 'bg-blue-700 hover:bg-blue-600'} text-white"
        onclick={(e) => { e.stopPropagation(); handlePlay(); }}
      >
        {running ? "Stop" : "Play"}
      </button>
    </div>

  {:else if mode === "blocks"}
    <div class="flex flex-col items-center p-3 gap-2 w-36">
      <img src={iconUrl} alt="" class="w-16 h-16 rounded object-cover" />
      <div class="text-xs text-center font-medium leading-tight line-clamp-2">{game.title}</div>
      <button
        class="px-3 py-1 rounded text-xs font-medium {running ? 'bg-red-700 hover:bg-red-600' : 'bg-blue-700 hover:bg-blue-600'} text-white"
        onclick={(e) => { e.stopPropagation(); handlePlay(); }}
      >
        {running ? "Stop" : "Play"}
      </button>
    </div>

  {:else if mode === "banners"}
    <div class="flex flex-col items-center gap-1 w-36">
      <img src={game.banner || iconUrl} alt="" class="w-36 h-52 rounded object-cover" />
      <div class="text-xs text-center font-medium leading-tight line-clamp-2 px-1">{game.title}</div>
      <button
        class="px-3 py-1 rounded text-xs font-medium {running ? 'bg-red-700 hover:bg-red-600' : 'bg-blue-700 hover:bg-blue-600'} text-white"
        onclick={(e) => { e.stopPropagation(); handlePlay(); }}
      >
        {running ? "Stop" : "Play"}
      </button>
    </div>
  {/if}

  <!-- Context menu -->
  {#if contextOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="absolute z-50 top-full left-0 mt-1 w-44 bg-surface-800 border border-surface-700 rounded shadow-lg py-1 text-sm" onclick={(e) => e.stopPropagation()} onmouseleave={closeContext}>
      <button class="w-full text-left px-3 py-1.5 hover:bg-surface-700" onclick={() => { handlePlay(); closeContext(); }}>
        {running ? "Stop" : "Play"}
      </button>
      <button class="w-full text-left px-3 py-1.5 hover:bg-surface-700" onclick={closeContext}>
        Edit
      </button>
      <button class="w-full text-left px-3 py-1.5 hover:bg-surface-700 text-red-400" onclick={() => { handleDelete(); closeContext(); }}>
        Delete
      </button>
    </div>
  {/if}

  {#if running}
    <div class="absolute top-1 right-1 w-2 h-2 rounded-full bg-green-500"></div>
  {/if}
</div>
