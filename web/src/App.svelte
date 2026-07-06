<script lang="ts">
  import { onMount } from "svelte";
  import { Toaster, toast } from "svelte-sonner";
  import Sidebar from "./lib/components/Sidebar.svelte";
  import Library from "./pages/Library.svelte";
  import Settings from "./pages/Settings.svelte";
  import GameForm from "./pages/GameForm.svelte";
  import ProtonManager from "./pages/ProtonManager.svelte";
  import LogViewer from "./pages/LogViewer.svelte";
  import type { GameResponse } from "./lib/api/types";
  import * as api from "./lib/api/client";

  let currentPage = $state<"library" | "settings" | "add" | "edit" | "proton" | "logs">("library");
  let games = $state<GameResponse[]>([]);
  let loading = $state(true);
  let editingGame = $state<GameResponse | null>(null);
  let logGameId = $state<string>("");
  let sidebarCollapsed = $state(false);

  onMount(async () => {
    await loadGames();
  });

  async function loadGames() {
    loading = true;
    try {
      console.log("[faugus] Loading games...");
      games = await api.listGames({ sort: "alpha" });
      console.log(`[faugus] Loaded ${games.length} games`);
    } catch (e: any) {
      console.error("[faugus] Failed to load games:", e);
      toast.error(e?.message || "Failed to load games");
    } finally {
      loading = false;
      console.log("[faugus] Loading complete, games:", games.length);
    }
  }

  function handleAdd() {
    editingGame = null;
    currentPage = "add";
  }

  function handleEdit(game: GameResponse) {
    editingGame = game;
    currentPage = "edit";
  }

  function handleShowLogs(gameid: string) {
    logGameId = gameid;
    currentPage = "logs";
  }

  async function handleSaved() {
    currentPage = "library";
    await loadGames();
  }
</script>

<Toaster position="top-right" richColors />

<div class="flex h-screen bg-surface-950 text-white overflow-hidden">
  <Sidebar {sidebarCollapsed} {currentPage} onNavigate={(p) => (currentPage = p)} onToggle={() => (sidebarCollapsed = !sidebarCollapsed)} />

  {#key currentPage}
  <div class="flex-1 flex flex-col overflow-hidden page-enter">
    {#if currentPage === "library"}
      <Library {games} {loading} onrefresh={loadGames} onadd={handleAdd} onedit={handleEdit} onshowlogs={handleShowLogs} />
    {:else if currentPage === "settings"}
      <Settings onback={() => (currentPage = "library")} />
    {:else if currentPage === "add" || currentPage === "edit"}
      <GameForm game={editingGame} oncancel={() => (currentPage = "library")} onsaved={handleSaved} />
    {:else if currentPage === "proton"}
      <ProtonManager onback={() => (currentPage = "library")} />
    {:else if currentPage === "logs"}
      <LogViewer gameid={logGameId} onback={() => (currentPage = "library")} />
    {/if}
  </div>
{/key}
</div>
