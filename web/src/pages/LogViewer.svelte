<script lang="ts">
  let { gameid, onback }: { gameid: string; onback: () => void } = $props();
</script>
<div class="p-6"><h2 class="text-xl font-bold mb-4">Log Viewer: {gameid}</h2><button class="px-4 py-2 rounded bg-blue-600 text-white" onclick={onback}>Back</button></div>
