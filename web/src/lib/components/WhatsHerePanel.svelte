<script lang="ts">
  import type { Workspace } from '../workspace/state.svelte';
  import type { Dataset, MapAction } from '../field/types';
  import { KINDS, KIND_LABELS, datasetDetail, groupDatasets, kindOf, type Kind } from '../field/datasets';
  // onask: put a request in the chat and send it (adding a table goes through the data agent).
  let { workspace, onask }: { workspace: Workspace; onask?: (text: string) => void } = $props();

  const PAGE = 8;  // rows shown per regime before "more"
  const datasets = $derived(workspace.field?.datasets ?? []);
  let query = $state('');
  // Tables (VizieR catalogues without a catalogue HiPS) number in the thousands: off until asked for.
  let kinds = $state<Kind[]>(['image', 'drawable', 'cube']);
  let open = $state<Record<string, number>>({});
  const all = $derived(groupDatasets(datasets, query));
  const groups = $derived(groupDatasets(datasets, query, kinds));
  const totals = $derived(Object.fromEntries(KINDS.map((k) => [k, all.reduce((n, g) => n + g.counts[k], 0)])) as Record<Kind, number>);
  const shownContext = $derived(new Set((workspace.map.context ?? []).map((c) => c.id)));
  const coverage = $derived(new Map((workspace.map.coverage ?? []).map((c) => [c.id, c.color])));

  const act = (action: MapAction) => workspace.request([action], 'user');
  const toggleKind = (kind: Kind) => (kinds = kinds.includes(kind) ? kinds.filter((k) => k !== kind) : [...kinds, kind]);
  const add = (d: Dataset) => onask?.(`Add the catalogue ${d.title} (${d.id}) to the field.`);
</script>

<section class="whats-here" aria-label="What's here">
  {#if !workspace.field}
    <p class="empty-state">Load a field to see every survey and catalogue that covers it.</p>
  {:else if workspace.datasetsStatus === 'loading' && !datasets.length}
    <p class="muted">Asking CDS what covers {workspace.field.target.name}…</p>
  {:else if workspace.datasetsStatus === 'failed' && !datasets.length}
    <p class="muted">Could not reach the CDS MOC server; the field's own data is unaffected.</p>
  {:else}
    <div class="whats-here-bar">
      <label class="sr-only" for="whats-here-search">Search datasets</label>
      <input id="whats-here-search" bind:value={query} placeholder="Search: eROSITA, radio, 2MASS, DES…" />
      {#each KINDS as kind}
        <button class="chip" aria-pressed={kinds.includes(kind)} onclick={() => toggleKind(kind)}>
          {KIND_LABELS[kind]} <small>{totals[kind]}</small>
        </button>
      {/each}
      <small class="muted">{datasets.length} datasets cover this field · CDS MOC server</small>
    </div>
    {#if !groups.length}<p class="muted">Nothing matches.</p>{/if}
    {#each groups as group (group.regime)}
      {@const limit = open[group.regime] ?? PAGE}
      <details open>
        <summary class="eyebrow">{group.regime.toUpperCase()} · {group.datasets.length}</summary>
        <ul class="dataset-list">
          {#each group.datasets.slice(0, limit) as d (d.id)}
            {@const kind = kindOf(d)}
            {@const color = coverage.get(d.id)}
            <li class="dataset">
              <div class="dataset-name">
                <strong>{d.title}</strong>
                <small class="muted">{d.id}{datasetDetail(d) ? ` · ${datasetDetail(d)}` : ''}</small>
              </div>
              <div class="dataset-actions">
                {#if kind === 'image'}
                  <button class="small-button" aria-pressed={workspace.survey === d.id} title="Show as the map's background"
                    onclick={() => act({ type: 'background.set', id: d.id })}>{workspace.survey === d.id ? 'Viewing' : 'View'}</button>
                {:else if kind === 'drawable'}
                  <button class="small-button" aria-pressed={shownContext.has(d.id)} title="Draw the whole catalogue from CDS (display only)"
                    onclick={() => act(shownContext.has(d.id) ? { type: 'context.hide', id: d.id } : { type: 'context.show', id: d.id })}>
                    {shownContext.has(d.id) ? 'On map' : 'Show'}</button>
                {:else if kind === 'table' && onask}
                  <button class="small-button" title="Ask the data agent to add it to the field" onclick={() => add(d)}>Add</button>
                {/if}
                <button class="small-button" aria-pressed={!!color} title="Outline where it has data"
                  onclick={() => act(color ? { type: 'coverage.hide', id: d.id } : { type: 'coverage.show', id: d.id })}>
                  {#if color}<span class="swatch" style:background={color}></span>{/if}Coverage</button>
              </div>
            </li>
          {/each}
        </ul>
        {#if group.datasets.length > limit}
          <button class="text-button" onclick={() => (open = { ...open, [group.regime]: limit + 4 * PAGE })}>
            {group.datasets.length - limit} more</button>
        {/if}
      </details>
    {/each}
  {/if}
</section>
