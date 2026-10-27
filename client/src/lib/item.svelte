<script>
	let { item } = $props();

	let latestHistory = $derived(item.history.at(-1));
	let status = $derived(latestHistory.status);
	let created_time = $derived(item.history.at(0).time ? new Date(item.history.at(0).time) : null);
	let updated_time = $derived(latestHistory.time ? new Date(latestHistory.time) : null);
</script>

<div class="food-item">
    <div>
        <div class="title">
            {item.name}
        </div>
        <div class="status {status}">{status?.replace('_', ' ')}</div>
    </div>
    <div class="details">
        <div>
            Item ID: <span>{item.id ?? '--'}</span>
        </div>
        <div>Source ID: <span>{item.source_id ?? '--'}</span></div>
        <div>Created At: <span>{created_time?.toLocaleString() ?? '--'}</span></div>
        {#if created_time?.getTime() !== updated_time?.getTime()}
            <div>Updated At: <span>{updated_time?.toLocaleString() ?? '--'}</span></div>
        {/if}
        <div>Price: <span>${item.price ?? '--'}</span></div>
        <div>Category: <span>{item.category ?? '--'}</span></div>
        <details>
            <summary>History ({item.history.length})</summary>
            <div class="history-list">
                {#each item.history as event (event.time)}
                    {@const time = new Date(event.time)?.toLocaleString() ?? 'unknown'}
                    <div>
                        <div>{event.status}</div>
                        <div>{time}</div>
                    </div>
                {/each}
            </div>
        </details>
    </div>
</div>

<style>
	.food-item {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
		border-radius: 0.5em;
		padding: 1em;
		font-family: monospace;
		font-weight: 600;
		background-color: var(--color-background);

		span {
			font-weight: 400;
			text-transform: uppercase;
		}
	}

    .title {
        font-size: 1.2em;
        margin-bottom: 1rem;
        margin-left: 0.25rem;
    }

    .status {
        background-color: darkgrey;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        width: fit-content;
        text-transform: capitalize;

        &.processing {
            background-color: purple;
            color: white;
        }

        &.with_courier {
            background-color: teal;
            color: white;
        }

        &.delivered {
            background-color: darkgreen;
            color: white;
        }
    }

    .details {
        display: flex;
        flex-direction: column;

        > div {
            width: fit-content;
            text-wrap-mode: wrap;
        }
    }

    .history-list {
        display: flex;
        flex-direction: column;
        width: fit-content;
        border: 2px solid var(--color-primary);
        padding: 0.5rem;
        margin-top: 0.5rem;

        > div {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 1rem;
            justify-content: space-between;

            div {
                text-align: right;
            }
        }
    }
</style>
