<script lang="ts">
  let { game, oncancel, onsaved }: { game: any; oncancel: () => void; onsaved: () => void } = $props();
</script>
<div class="p-6"><h2 class="text-xl font-bold mb-4">Game Form (TODO)</h2><button class="px-4 py-2 rounded bg-blue-600 text-white" onclick={oncancel}>Back</button></div>
