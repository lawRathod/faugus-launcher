<script lang="ts">
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";
  import { ArrowLeft, Copy, FileText, ExternalLink } from "lucide-svelte";
  import * as api from "../lib/api/client";

  let { gameid, onback }: { gameid: string; onback: () => void } = $props();

  let tab = $state(0);
  let protonLog = $state("");
  let umuLog = $state("");
  let loading = $state(true);

  onMount(async () => {
    try {
      const logs = await api.getGameLogs(gameid);
      protonLog = logs.proton_log || "No Proton log found.";
      umuLog = logs.umu_log || "No UMU log found.";
    } catch {
      protonLog = "Failed to load logs.";
      umuLog = "";
    } finally {
      loading = false;
    }
  });

  function copyLog() {
    const text = tab === 0 ? protonLog : umuLog;
    navigator.clipboard.writeText(text).then(() => toast.success("Copied!"));
  }
</script>

<div class="flex flex-col h-full">
  <div class="flex items-center gap-3 px-4 py-2.5 border-b border-surface-800 bg-surface-900/50 shrink-0">
    <button class="p-1.5 rounded-lg hover:bg-surface-800 text-gray-400" onclick={onback}><ArrowLeft size={18} /></button>
    <h2 class="text-lg font-bold">Logs: {gameid}</h2>
    <div class="flex-1" />
    <button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm" onclick={copyLog}><Copy size={14} /> Copy</button>
  </div>

  <div class="flex gap-0 px-4 bg-surface-900 border-b border-surface-800">
    <button class="px-4 py-2 text-sm font-medium border-b-2 {tab === 0 ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-500'}" onclick={() => (tab = 0)}>Proton</button>
    <button class="px-4 py-2 text-sm font-medium border-b-2 {tab === 1 ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-500'}" onclick={() => (tab = 1)}>UMU-Launcher</button>
  </div>

  <div class="flex-1 overflow-y-auto p-4">
    {#if loading}
      <div class="flex items-center justify-center h-full"><div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" /></div>
    {:else}
      <pre class="text-xs text-gray-300 font-mono whitespace-pre-wrap bg-surface-900 rounded-lg p-4 border border-surface-800 max-h-full overflow-auto">{tab === 0 ? protonLog : umuLog}</pre>
    {/if}
  </div>
</div>
