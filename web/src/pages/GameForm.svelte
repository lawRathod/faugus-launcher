<script lang="ts">
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";
  import { ArrowLeft, Save, Image, X } from "lucide-svelte";
  import type { GameResponse } from "../lib/api/types";
  import * as api from "../lib/api/client";

  let { game, oncancel, onsaved }: { game: GameResponse | null; oncancel: () => void; onsaved: () => void } = $props();

  let tab = $state(0);
  let saving = $state(false);
  let title = $state(game?.title ?? "");
  let path = $state(game?.path ?? "");
  let prefix = $state(game?.prefix ?? "");
  let runner = $state(game?.runner ?? "");
  let launchArgs = $state(game?.launch_arguments ?? "");
  let gameArgs = $state(game?.game_arguments ?? "");
  let protonfix = $state(game?.protonfix ?? "");
  let mangohud = $state(game?.mangohud === "True" || game?.mangohud === true);
  let gamemode = $state(game?.gamemode === "True" || game?.gamemode === true);
  let disableHidraw = $state(game?.disable_hidraw === "True" || game?.disable_hidraw === true);
  let preventSleep = $state(game?.prevent_sleep === true);
  let iconPreview = $state(game?.icon ?? "");
  let bannerPreview = $state(game?.banner ?? "");
  let shortcutDesktop = $state(false);
  let shortcutAppmenu = $state(false);
  let shortcutSteam = $state(false);
  let runners = $state<{ name: string; path: string }[]>([]);
  let steamGames = $state<{ appid: string; name: string }[]>([]);

  let isEdit = $derived(game !== null && game !== undefined);

  onMount(async () => {
    try {
      runners = await api.listRunners();
    } catch {}
    try {
      steamGames = await api.listSteamGames();
    } catch {}
  });

  async function handleSave() {
    if (!title.trim()) { toast.error("Title is required"); return; }
    if (!path.trim()) { toast.error("Path is required"); return; }
    if (!prefix.trim()) { toast.error("Prefix is required"); return; }

    saving = true;
    try {
      const data = {
        title: title.trim(),
        path: path.trim(),
        prefix: prefix.trim(),
        runner,
        launch_arguments: launchArgs,
        game_arguments: gameArgs,
        protonfix,
        mangohud,
        gamemode,
        disable_hidraw: disableHidraw,
        prevent_sleep: preventSleep,
        icon: iconPreview,
        banner: bannerPreview,
      };

      if (isEdit) {
        await api.updateGame(game!.gameid, data);
        toast.success("Game updated");
      } else {
        await api.createGame(data);
        toast.success("Game created");
      }
      onsaved();
    } catch (e: any) {
      toast.error(e.message || "Failed to save game");
    } finally {
      saving = false;
    }
  }

  async function handleIconUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files?.length) return;
    try {
      const result = await api.uploadIcon(title.trim() || "temp", input.files[0]);
      iconPreview = result.path;
      toast.success("Icon uploaded");
    } catch {
      toast.error("Failed to upload icon");
    }
  }

  async function handleBannerUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files?.length) return;
    try {
      const result = await api.uploadBanner(title.trim() || "temp", input.files[0]);
      bannerPreview = result.path;
      toast.success("Banner uploaded");
    } catch {
      toast.error("Failed to upload banner");
    }
  }
</script>

<div class="flex flex-col h-full">
  <!-- Header -->
  <div class="flex items-center gap-3 px-4 py-2.5 border-b border-surface-800 bg-surface-900/50">
    <button class="p-1.5 rounded-lg hover:bg-surface-800 text-gray-400" onclick={oncancel}><ArrowLeft size={18} /></button>
    <h2 class="text-lg font-bold">{isEdit ? "Edit" : "Add"} Game</h2>
    <div class="flex-1"></div>
    <button class="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium disabled:opacity-50" disabled={saving} onclick={handleSave}>
      <Save size={16} /> {saving ? "Saving..." : "Save"}
    </button>
  </div>

  <!-- Tabs -->
  <div class="flex gap-0 px-4 pt-3 border-b border-surface-800 bg-surface-900">
    <button class="px-4 py-2 text-sm font-medium border-b-2 transition-colors {tab === 0 ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-300'}" onclick={() => (tab = 0)}>Game / App</button>
    <button class="px-4 py-2 text-sm font-medium border-b-2 transition-colors {tab === 1 ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-300'}" onclick={() => (tab = 1)}>Tools</button>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-y-auto p-4">
    {#if tab === 0}
      <div class="max-w-2xl space-y-4">
        <div>
          <label class="block text-sm text-gray-400 mb-1">Title</label>
          <input class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm focus:outline-none focus:border-blue-500" bind:value={title} placeholder="Game Title" />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Path (.exe)</label>
          <input class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm focus:outline-none focus:border-blue-500" bind:value={path} placeholder="/path/to/game.exe" />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Prefix</label>
          <input class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm focus:outline-none focus:border-blue-500" bind:value={prefix} placeholder="/home/user/Faugus/mygame" />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Proton Runner</label>
          <select class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm focus:outline-none focus:border-blue-500" bind:value={runner}>
            <option value="">Default</option>
            {#each runners as r}
              <option value={r.name}>{r.name}</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Launch Arguments</label>
          <input class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm focus:outline-none focus:border-blue-500 font-mono" bind:value={launchArgs} placeholder="PROTON_USE_WINED3D=1 gamescope -W 2560 -H 1440" />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Game Arguments</label>
          <input class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm focus:outline-none focus:border-blue-500" bind:value={gameArgs} placeholder="-d3d11 -fullscreen" />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Protonfix / UMU ID</label>
          <input class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm focus:outline-none focus:border-blue-500" bind:value={protonfix} placeholder="e.g. 12345" />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-400 mb-1">Icon</label>
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-lg bg-surface-800 border border-surface-700 flex items-center justify-center overflow-hidden">
                {#if iconPreview}<img src={iconPreview} alt="" class="w-full h-full object-cover" />
                {:else}<Image size={20} class="text-gray-600" />{/if}
              </div>
              <input type="file" accept="image/png,image/ico" class="text-sm text-gray-400 file:mr-2 file:px-3 file:py-1 file:rounded file:border-0 file:text-sm file:bg-surface-800 file:text-white hover:file:bg-surface-700" onchange={handleIconUpload} />
            </div>
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Banner</label>
            <div class="flex items-center gap-3">
              <div class="w-12 h-16 rounded-lg bg-surface-800 border border-surface-700 flex items-center justify-center overflow-hidden">
                {#if bannerPreview}<img src={bannerPreview} alt="" class="w-full h-full object-cover" />
                {:else}<Image size={20} class="text-gray-600" />{/if}
              </div>
              <input type="file" accept="image/png" class="text-sm text-gray-400 file:mr-2 file:px-3 file:py-1 file:rounded file:border-0 file:text-sm file:bg-surface-800 file:text-white hover:file:bg-surface-700" onchange={handleBannerUpload} />
            </div>
          </div>
        </div>

        {#if steamGames.length > 0}
          <div>
            <label class="block text-sm text-gray-400 mb-1">Import from Steam</label>
            <select class="w-full px-3 py-2 rounded-lg bg-surface-800 border border-surface-700 text-white text-sm" onchange={(e) => {
              const sel = steamGames.find(s => s.appid === e.currentTarget.value);
              if (sel) { title = sel.name; }
            }}>
              <option value="">Select a Steam game...</option>
              {#each steamGames as sg}
                <option value={sg.appid}>{sg.name}</option>
              {/each}
            </select>
          </div>
        {/if}
      </div>

    {:else if tab === 1}
      <div class="max-w-2xl space-y-4">
        <h3 class="text-sm font-semibold text-gray-400 uppercase">Prefix Tools</h3>
        <div class="flex gap-2">
          <button class="px-4 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Winecfg</button>
          <button class="px-4 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Winetricks</button>
          <button class="px-4 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Run...</button>
        </div>

        <h3 class="text-sm font-semibold text-gray-400 uppercase pt-2">Toggles</h3>
        <label class="flex items-center gap-3 text-sm">
          <input type="checkbox" bind:checked={mangohud} class="rounded bg-surface-800 border-surface-600" />
          MangoHUD
        </label>
        <label class="flex items-center gap-3 text-sm">
          <input type="checkbox" bind:checked={gamemode} class="rounded bg-surface-800 border-surface-600" />
          GameMode
        </label>
        <label class="flex items-center gap-3 text-sm">
          <input type="checkbox" bind:checked={disableHidraw} class="rounded bg-surface-800 border-surface-600" />
          Disable Hidraw
        </label>
        <label class="flex items-center gap-3 text-sm">
          <input type="checkbox" bind:checked={preventSleep} class="rounded bg-surface-800 border-surface-600" />
          Prevent Sleep
        </label>

        <h3 class="text-sm font-semibold text-gray-400 uppercase pt-2">Shortcuts</h3>
        <label class="flex items-center gap-3 text-sm">
          <input type="checkbox" bind:checked={shortcutDesktop} class="rounded bg-surface-800 border-surface-600" />
          Desktop shortcut
        </label>
        <label class="flex items-center gap-3 text-sm">
          <input type="checkbox" bind:checked={shortcutAppmenu} class="rounded bg-surface-800 border-surface-600" />
          App menu shortcut
        </label>
        <label class="flex items-center gap-3 text-sm">
          <input type="checkbox" bind:checked={shortcutSteam} class="rounded bg-surface-800 border-surface-600" />
          Steam shortcut
        </label>

        <div class="pt-2">
          <button class="px-4 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Additional Application...</button>
          <button class="ml-2 px-4 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 text-white text-sm border border-surface-700">Lossless Scaling...</button>
        </div>
      </div>
    {/if}
  </div>
</div>
