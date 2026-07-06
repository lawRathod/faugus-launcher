<script lang="ts">
  import { Gamepad2, Settings as SettingsIcon, Library as LibraryIcon, ChevronLeft, ChevronRight } from "lucide-svelte";

  let {
    sidebarCollapsed,
    currentPage,
    onNavigate,
    onToggle,
  }: {
    sidebarCollapsed: boolean;
    currentPage: string;
    onNavigate: (page: string) => void;
    onToggle: () => void;
  } = $props();
</script>

<aside
  class="flex flex-col bg-surface-900 border-r border-surface-800 transition-all duration-200 shrink-0"
  class:w-56={!sidebarCollapsed}
  class:w-16={sidebarCollapsed}
>
  <div class="flex items-center gap-3 px-4 h-14 border-b border-surface-800" class:justify-center={sidebarCollapsed}>
    {#if !sidebarCollapsed}
      <Gamepad2 class="text-blue-400" size={24} />
      <span class="font-bold text-white">Faugus</span>
    {:else}
      <Gamepad2 class="text-blue-400" size={24} />
    {/if}
  </div>

  <nav class="flex-1 px-2 py-4 flex flex-col gap-1">
    <button
      class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
      class:bg-surface-800={currentPage === "library"}
      class:justify-center={sidebarCollapsed}
      style={currentPage === "library" ? "color: #60a5fa" : "color: #9ca3af"}
      onclick={() => onNavigate("library")}
    >
      <LibraryIcon size={20} />
      {#if !sidebarCollapsed}<span>Library</span>{/if}
    </button>

    <button
      class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
      class:bg-surface-800={currentPage === "settings"}
      class:justify-center={sidebarCollapsed}
      style={currentPage === "settings" ? "color: #60a5fa" : "color: #9ca3af"}
      onclick={() => onNavigate("settings")}
    >
      <SettingsIcon size={20} />
      {#if !sidebarCollapsed}<span>Settings</span>{/if}
    </button>

    <button
      class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
      class:bg-surface-800={currentPage === "proton"}
      class:justify-center={sidebarCollapsed}
      style={currentPage === "proton" ? "color: #60a5fa" : "color: #9ca3af"}
      onclick={() => onNavigate("proton")}
    >
      <Gamepad2 size={20} />
      {#if !sidebarCollapsed}<span>Proton Manager</span>{/if}
    </button>
  </nav>

  <div class="px-2 py-3 border-t border-surface-800">
    <button class="flex items-center justify-center w-full py-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors" onclick={onToggle}>
      {#if sidebarCollapsed}<ChevronRight size={18} />{:else}<ChevronLeft size={18} />{/if}
    </button>
  </div>
</aside>
