<script lang="ts">
  import { onMount } from "svelte";
  import Library from "./pages/Library.svelte";
  import Settings from "./pages/Settings.svelte";
  import { GameState, type GameResponse } from "./lib/api/types";

  let currentPage = $state<"library" | "settings">("library");
  let games = $state<GameResponse[]>([]);
  let loading = $state(true);

  onMount(async () => {
    await loadGames();
  });

  async function loadGames() {
    loading = true;
    try {
      const resp = await fetch("/api/games?sort=alpha");
      games = await resp.json();
    } catch (e) {
      console.error("Failed to load games:", e);
    } finally {
      loading = false;
    }
  }

  function navigate(page: "library" | "settings") {
    currentPage = page;
  }
</script>

<div class="flex h-screen flex-col">
  <!-- Title bar -->
  <header class="flex items-center justify-between bg-surface-900 px-4 py-2 border-b border-surface-800" data-tauri-drag-region>
    <h1 class="text-lg font-bold text-white">Faugus Launcher</h1>
    <nav class="flex gap-2">
      <button
        class="px-3 py-1 rounded text-sm {currentPage === 'library' ? 'bg-blue-600 text-white' : 'bg-surface-800 text-gray-300 hover:bg-surface-700'}"
        onclick={() => navigate("library")}
      >
        Library
      </button>
      <button
        class="px-3 py-1 rounded text-sm {currentPage === 'settings' ? 'bg-blue-600 text-white' : 'bg-surface-800 text-gray-300 hover:bg-surface-700'}"
        onclick={() => navigate("settings")}
      >
        Settings
      </button>
    </nav>
  </header>

  <!-- Main content -->
  <main class="flex-1 overflow-hidden">
    {#if currentPage === "library"}
      <Library {games} {loading} onrefresh={loadGames} />
    {:else}
      <Settings />
    {/if}
  </main>
</div>
