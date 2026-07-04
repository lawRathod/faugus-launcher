<script lang="ts">
  import { onMount } from "svelte";
  import type { ConfigResponse } from "../lib/api/types";
  import { getConfig, updateConfig } from "../lib/api/client";

  let config = $state<ConfigResponse>({});
  let saving = $state(false);

  onMount(async () => {
    config = await getConfig();
  });

  async function save() {
    saving = true;
    try {
      config = await updateConfig(config);
    } catch (e) {
      console.error("Failed to save config:", e);
    } finally {
      saving = false;
    }
  }
</script>

<div class="p-6 overflow-y-auto h-full">
  <h2 class="text-xl font-bold mb-4">Settings</h2>

  <div class="grid grid-cols-3 gap-6 max-w-4xl">
    <!-- Column 1 -->
    <div class="flex flex-col gap-4">
      <h3 class="text-sm font-semibold text-gray-400 uppercase">Interface</h3>
      <div class="flex flex-col gap-2">
        <label class="flex items-center gap-2 text-sm">
          <span class="w-24 text-gray-400">Mode</span>
          <select class="flex-1 px-2 py-1 rounded bg-surface-800 border border-surface-700" bind:value={config["interface-mode"]}>
            <option value="List">List</option>
            <option value="Blocks">Blocks</option>
            <option value="Banners">Banners</option>
          </select>
        </label>
      </div>
    </div>

    <!-- Column 2 -->
    <div class="flex flex-col gap-4">
      <h3 class="text-sm font-semibold text-gray-400 uppercase">Proton</h3>
      <label class="flex items-center gap-2 text-sm">
        <span class="w-24 text-gray-400">Default</span>
        <input class="flex-1 px-2 py-1 rounded bg-surface-800 border border-surface-700" bind:value={config["default-runner"]} />
      </label>
    </div>

    <!-- Column 3 -->
    <div class="flex flex-col gap-4">
      <h3 class="text-sm font-semibold text-gray-400 uppercase">Misc</h3>
      <label class="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={config["mangohud"] === "True"} onchange={(e) => (config["mangohud"] = e.currentTarget.checked ? "True" : "False")} />
        <span>MangoHUD</span>
      </label>
      <label class="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={config["gamemode"] === "True"} onchange={(e) => (config["gamemode"] = e.currentTarget.checked ? "True" : "False")} />
        <span>GameMode</span>
      </label>
      <label class="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={config["system-tray"] === "True"} onchange={(e) => (config["system-tray"] = e.currentTarget.checked ? "True" : "False")} />
        <span>System tray</span>
      </label>
    </div>
  </div>

  <div class="mt-6">
    <button
      class="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-sm disabled:opacity-50"
      disabled={saving}
      onclick={save}
    >
      {saving ? "Saving..." : "Save Settings"}
    </button>
  </div>
</div>
