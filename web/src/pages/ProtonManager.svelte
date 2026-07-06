<script lang="ts">
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";
  import { ArrowLeft, Download, RefreshCw } from "lucide-svelte";
  import * as api from "../lib/api/client";
  import type { RunnerInfo, RunnerVariant } from "../lib/api/types";

  let { onback }: { onback: () => void } = $props();

  let tab = $state(0);
  let runners = $state<RunnerInfo[]>([]);
  let variants = $state<RunnerVariant[]>([]);
  let loading = $state(true);

  const variantKeys = ["cachyos", "ge", "em", "dw"];
  const variantLabels = ["Proton-CachyOS", "GE-Proton", "Proton-EM", "DW-Proton"];

  onMount(async () => {
    try {
      [runners, variants] = await Promise.all([api.listRunners(), api.getLatestRunnerVersions()]);
    } catch {
      toast.error("Failed to load runners");
    } finally {
      loading = false;
    }
  });

  function getLatest(key: string): string | null {
    return variants.find(v => v.key === key)?.latest_version ?? null;
  }

  function getInstalled(key: string): RunnerInfo[] {
    return runners.filter(r => r.type === key);
  }
</script>

<div class="flex flex-col h-full">
  <div class="flex items-center gap-3 px-4 py-2.5 border-b border-surface-800 bg-surface-900/50 shrink-0">
    <button class="p-1.5 rounded-lg hover:bg-surface-800 text-gray-400" onclick={onback}><ArrowLeft size={18} /></button>
    <h2 class="text-lg font-bold">Proton Manager</h2>
    <div class="flex-1"></div>
  </div>

  <div class="flex gap-0 px-4 bg-surface-900 border-b border-surface-800 overflow-x-auto">
    {#each variantLabels as label, i}
      <button class="px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap {tab === i ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-300'}" onclick={() => (tab = i)}>{label}</button>
    {/each}
  </div>

  <div class="flex-1 overflow-y-auto p-4">
    {#if loading}
      <div class="flex items-center justify-center h-full"><div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>
    {:else}
      <div class="max-w-2xl">
        <div class="flex items-center gap-3 mb-4">
          <h3 class="text-lg font-semibold">{variantLabels[tab]}</h3>
          {#if getLatest(variantKeys[tab])}
            <span class="px-2 py-0.5 rounded-full bg-green-900/50 text-green-400 text-xs">Latest: {getLatest(variantKeys[tab])}</span>
          {/if}
        </div>

        {#if getInstalled(variantKeys[tab]).length === 0}
          <p class="text-gray-500 text-sm mb-4">No versions installed.</p>
        {:else}
          <div class="space-y-2 mb-4">
            {#each getInstalled(variantKeys[tab]) as runner}
              <div class="flex items-center justify-between px-3 py-2 rounded-lg bg-surface-800 border border-surface-700">
                <div>
                  <span class="text-sm text-white">{runner.name}</span>
                  {#if runner.is_latest}<span class="ml-2 px-1.5 py-0.5 rounded bg-blue-900/50 text-blue-400 text-xs">Latest</span>{/if}
                </div>
                <span class="text-xs text-gray-500">{runner.path}</span>
              </div>
            {/each}
          </div>
        {/if}

        <button class="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium disabled:opacity-50" disabled={!getLatest(variantKeys[tab])}>
          <Download size={16} /> Download {getLatest(variantKeys[tab]) || "..."}
        </button>
      </div>
    {/if}
  </div>
</div>
