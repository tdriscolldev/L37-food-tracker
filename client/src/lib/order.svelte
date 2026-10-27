<script>
    let {order} = $props();

    let created_time = $derived(order.created_at ? new Date(order.created_at) : null);
    let updated_time = $derived(order.updated_at ? new Date(order.updated_at) : null);
    let scheduled_time = $derived(order.scheduled_for ? new Date(order.scheduled_for) : null);
</script>

<div class="order">
    <div>Order ID: <span>{order.id ?? '--'}</span></div>
    <div>Created At: <span>{created_time?.toLocaleString() ?? '--'}</span></div>
    {#if created_time?.getTime() !== updated_time?.getTime()}
        <div>Updated At: <span>{updated_time?.toLocaleString() ?? '--'}</span></div>
    {/if}
    <div>
        Source:
        <span>
            {order.source ?? '--'}
            {order.source_id ? order.source_id : ''}
        </span>
    </div>
    <div>Customer: <span>{order.customer_first_name} {order.customer_last_name}</span></div>
    <div>Restaurant: <span>{order.restaurant ?? '--'}</span></div>
    <div>Total: <span>${order.total_price_usd ?? '--'}</span></div>
    <div>Customer Notes: <span>{order.notes ?? '--'}</span></div>
    <div>Scheduled: <span>{scheduled_time?.toLocaleString() ?? '--'}</span></div>
    <div>Items({order.items?.length ?? '?'}):</div>
    <div class="food-item-list">
        {#each order.items as item}
            {@const status = item.history.at(-1).status}
            <div class="food-item">
                <div class="status {status}">{status?.replace("_", " ")}</div>
                <span>{item.name}</span>
                <span>{item.price ? '$' + item.price : ''}</span>
            </div>
        {/each}
    </div>
</div>

<style>
    .order {
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

	.food-item-list {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		margin-top: 0.25rem;
	}

	.food-item {
		display: grid;
		place-content: center;
		place-items: center;
		width: fit-content;
		grid-template-columns: auto auto auto;
		gap: 0.25rem;
		text-transform: capitalize;

		.status {
			background-color: darkgrey;
			padding: 0.25rem 0.5rem;
			border-radius: 9999px;

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
	}
</style>
