<script lang="ts">
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";
  import { ArrowLeft, Save, RefreshCw } from "lucide-svelte";
  import * as api from "../lib/api/client";
  import type { ConfigResponse, RunnerInfo } from "../lib/api/types";

  let { onback }: { onback: () => void } = $props();

  let config = $state<ConfigResponse>({});
  let runners = $state<RunnerInfo[]>([]);
  let saving = $state(false);
  let envarList = $state<string[]>([""]);

  onMount(async () => {
    try {
      config = await api.getConfig();
    } catch {}
    try {
      runners = await api.listRunners();
    } catch {}
    try {
      envarList = await api.getEnvar();
      if (envarList.length === 0) envarList = [""];
    } catch {}
  });

  async function save() {
    saving = true;
    try {
      config = await api.updateConfig(config);
      await api.setEnvar(envarList.filter(l => l.trim()));
      toast.success("Settings saved");
    } catch (e: any) {
      toast.error(e.message || "Failed to save");
    } finally {
      saving = false;
    }
  }

  async function createBackup() {
    try {
      const result = await api.createBackup();
      toast.success(`Backup created: ${result.date}`);
    } catch { toast.error("Backup failed"); }
  }

  async function handleRestore(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files?.length) return;
    try {
      await api.restoreBackup(input.files[0]);
      toast.success("Backup restored");
    } catch { toast.error("Restore failed"); }
  }

  function addEnvarRow() { envarList = [...envarList, ""]; }
  function removeEnvarRow(i: number) { envarList = envarList.filter((_, idx) => idx !== i); if (envarList.length === 0) envarList = [""]; }

  function boolVal(key: string): boolean {
    return config[key] === "True";
  }
  function setBool(key: string, val: boolean) {
    config[key] = val ? "True" : "False";
  }
</script>

<div class="flex flex-col h-full">
  <div class="flex items-center gap-3 px-4 py-2.5 border-b border-surface-800 bg-surface-900/50 shrink-0">
    <button class="p-1.5 rounded-lg hover:bg-surface-800 text-gray-400" onclick={onback}><ArrowLeft size={18} /></button>
    <h2 class="text-lg font-bold">Settings</h2>
    <div class="flex-1"></div>
    <button class="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium disabled:opacity-50" disabled={saving} onclick={save}>
      <Save size={16} /> {saving ? "Saving..." : "Save"}
    </button>
  </div>

  <div class="flex-1 overflow-y-auto p-6">
    <div class="max-w-4xl grid grid-cols-3 gap-8">
      <!-- Column 1 -->
      <div class="space-y-5">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">Interface</h3>
        <div class="space-y-3">
          <label class="block"><span class="text-sm text-gray-400 block mb-1">Mode</span>
            <select class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm" bind:value={config["interface-mode"]}>
              <option value="List">List</option>
              <option value="Blocks">Blocks</option>
              <option value="Banners">Banners</option>
            </select>
          </label>
          <label class="block"><span class="text-sm text-gray-400 block mb-1">Window behavior</span>
            <select class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm" bind:value={config["window-behavior"]}>
              <option value="None">Default</option>
              <option value="Remember">Remember</option>
              <option value="Maximized">Maximized</option>
              <option value="Fullscreen">Fullscreen</option>
            </select>
          </label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("show-labels")} onchange={(e) => setBool("show-labels", e.currentTarget.checked)} /> Show labels</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("show-categories")} onchange={(e) => setBool("show-categories", e.currentTarget.checked)} /> Show categories</label>
        </div>

        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider pt-2">Language</h3>
        <select class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm" bind:value={config.language}>
          <option value="en_US">English</option>
        </select>
      </div>

      <!-- Column 2 -->
      <div class="space-y-5">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">Prefixes</h3>
        <div class="space-y-3">
          <label class="block"><span class="text-sm text-gray-400 block mb-1">Default prefix location</span>
            <input class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm font-mono" bind:value={config["default-prefix"]} />
          </label>
          <label class="block"><span class="text-sm text-gray-400 block mb-1">Default Proton</span>
            <select class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm" bind:value={config["default-runner"]}>
              <option value="Proton-CachyOS Latest">Proton-CachyOS Latest</option>
              <option value="Proton-CachyOS (System)">Proton-CachyOS (System)</option>
              <option value="Proton-GE Latest">Proton-GE Latest</option>
              {#each runners as r}
                {#if !["Proton-CachyOS Latest", "Proton-CachyOS (System)", "Proton-GE Latest", "Proton-EM Latest", "DW-Proton Latest", "UMU-Launcher Latest"].includes(r.name)}
                  <option value={r.name}>{r.name}</option>
                {/if}
              {/each}
            </select>
          </label>
          <label class="block"><span class="text-sm text-gray-400 block mb-1">Lossless Scaling .dll</span>
            <input class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm font-mono" bind:value={config["lossless-location"]} />
          </label>
        </div>

        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider pt-2">Prefix Tools</h3>
        <div class="flex gap-2">
          <button class="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Winetricks</button>
          <button class="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Winecfg</button>
          <button class="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Run</button>
        </div>

        <div class="space-y-2 pt-2">
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("mangohud")} onchange={(e) => setBool("mangohud", e.currentTarget.checked)} /> MangoHUD</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("gamemode")} onchange={(e) => setBool("gamemode", e.currentTarget.checked)} /> GameMode</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("disable-hidraw")} onchange={(e) => setBool("disable-hidraw", e.currentTarget.checked)} /> Disable Hidraw</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("prevent-sleep")} onchange={(e) => setBool("prevent-sleep", e.currentTarget.checked)} /> Prevent Sleep</label>
        </div>
      </div>

      <!-- Column 3 -->
      <div class="space-y-5">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">Miscellaneous</h3>
        <div class="space-y-2">
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("discrete-gpu")} onchange={(e) => setBool("discrete-gpu", e.currentTarget.checked)} /> Use discrete GPU</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("close-onlaunch")} onchange={(e) => setBool("close-onlaunch", e.currentTarget.checked)} /> Close after launch</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("splash-disable")} onchange={(e) => setBool("splash-disable", e.currentTarget.checked)} /> Disable splash</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("disable-updates")} onchange={(e) => setBool("disable-updates", e.currentTarget.checked)} /> Disable updates</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("system-tray")} onchange={(e) => setBool("system-tray", e.currentTarget.checked)} /> System tray</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("enable-logging")} onchange={(e) => setBool("enable-logging", e.currentTarget.checked)} /> Enable logging</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("gamepad-navigation")} onchange={(e) => setBool("gamepad-navigation", e.currentTarget.checked)} /> Gamepad nav</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("wayland-driver")} onchange={(e) => setBool("wayland-driver", e.currentTarget.checked)} /> Wayland driver</label>
          <label class="flex items-center gap-3 text-sm"><input type="checkbox" class="rounded" checked={boolVal("enable-wow64")} onchange={(e) => setBool("enable-wow64", e.currentTarget.checked)} /> WOW64</label>
        </div>

        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider pt-2">Env Variables</h3>
        <div class="space-y-1">
          {#each envarList as env, i}
            <div class="flex gap-1">
              <input class="flex-1 px-2 py-1 rounded bg-surface-800 border border-surface-700 text-white text-sm font-mono" bind:value={envarList[i]} placeholder="KEY=VALUE" />
              <button class="px-2 py-1 rounded bg-red-900/50 hover:bg-red-800 text-red-300 text-sm" onclick={() => removeEnvarRow(i)}>×</button>
            </div>
          {/each}
          <button class="text-sm text-blue-400 hover:text-blue-300" onclick={addEnvarRow}>+ Add variable</button>
        </div>

        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider pt-2">Backup</h3>
        <div class="flex gap-2">
          <button class="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700" onclick={createBackup}>Create Backup</button>
          <label class="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700 cursor-pointer">
            Restore...
            <input type="file" accept=".zip" class="hidden" onchange={handleRestore} />
          </label>
        </div>

        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider pt-2">Proton Manager</h3>
        <button class="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Open Proton Manager</button>

        <div class="pt-4 flex gap-3">
          <a href="https://ko-fi.com/K3K10EMDU" target="_blank" class="flex-1 px-3 py-2 rounded-lg text-center text-sm font-medium bg-orange-600 hover:bg-orange-500 text-white">Ko-fi</a>
          <a href="https://www.paypal.com/donate/?business=57PP9DVD3VWAN" target="_blank" class="flex-1 px-3 py-2 rounded-lg text-center text-sm font-medium bg-blue-800 hover:bg-blue-700 text-white">PayPal</a>
        </div>
      </div>
    </div>
  </div>
</div>
