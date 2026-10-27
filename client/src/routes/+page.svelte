<script>
	import { onMount } from 'svelte';
	import { create_reconnecting_ws } from '#lib/reconnecting_websocket.js';

	const LIVE_PAGE_ORDER_MAX = 100;

	/**
	 * @type {Array<any>}
	 */
	let recentOrders = $state([]);
	let totalOrderCount = $state(0);
	let connected = $state(false);
	let fetchStatusMessage = $state('');
	let countStatusMessage = $state('');
	let wsStatusMessage = $state('');

	/**
	 * @type {FileList | null | undefined}
	 */
	let files = $state(null);

	const filterOrders = () => {
		// Trim back to max limit
		recentOrders = recentOrders
			.sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))
			.sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at))
			.slice(0, LIVE_PAGE_ORDER_MAX);
	};

	/**
	 * Load historical order data
	 */
	const fetchDB = async () => {
		try {
			fetchStatusMessage = '';
			const response = await fetch(`http://localhost:8000/api/db/orders/recent?limit=${LIVE_PAGE_ORDER_MAX}`);
			if (!response.ok) {
				console.log(`Failed to fetch: ${response.status}`);
				fetchStatusMessage = response.statusText;
				return;
			}

			const result = await response.json();
			console.log('Fetched entries: ', result);
			recentOrders = result;
			filterOrders();
		} catch (/** @type {any} */ error) {
			console.error(error.message);
			fetchStatusMessage = error.message;
		}
	};

	/**
	 * Load total order count
	 */
	const fetchCount = async () => {
		try {
			countStatusMessage = '';
			const response = await fetch(`http://localhost:8000/api/db/orders/count`);
			if (!response.ok) {
				console.log(`Failed to fetch: ${response.status}`);
				countStatusMessage = response.statusText;
				return;
			}

			const result = await response.json();
			console.debug('Fetched count: ', result);
			totalOrderCount = result;
		} catch (/** @type {any} */ error) {
			console.error(error.message);
			countStatusMessage = error.message;
		}
	};

	/**
	 * Upload CSV order data
	 */
	const uploadCSV = async () => {
		if (!files || files?.length === 0) {
			console.log('Failed to upload CSV: no file selected!');
			return;
		}
		let formData = new FormData();
		formData.append('file', files[0]);

		try {
			const response = await fetch(`http://localhost:8000/external/order/csv/upload`, {
				method: 'POST',
				body: formData
			});
			if (!response.ok) {
				console.log(`Failed to upload CSV data: ${response.status}`);
				return;
			}
		} catch (/** @type {any} */ error) {
			console.error(error.message);
		}
	};

	onMount(() => {
		// Fetch historical data
		fetchCount();
		fetchDB();

		// Create websocket for live updates
		const ws = create_reconnecting_ws('ws://localhost:8000/api/db/orders/ws');
		ws.onerror = (event) => {
			wsStatusMessage = `Error: ${JSON.stringify(event)}`;
		};
		ws.onopen = () => {
			console.log('Connected to live order updates');
			connected = true;
			wsStatusMessage = '';
		};
		ws.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data);
				console.debug('Received update for: ', data);

				let index = recentOrders.findIndex((order) => order.id == data.id);
				// Replace item in list
				if (index >= 0) {
					recentOrders[index] = data;
				} else {
					// Append to list
					recentOrders.push(data);
				}
				filterOrders();

				fetchCount();
			} catch (error) {
				console.error(`Failed to update order list: ${error}`);
			}
		};
		ws.onclose = () => {
			connected = false;
			wsStatusMessage = 'Websocket closed!';
		};

		return () => {
			ws.close();
		};
	});
</script>

<div class="content">
	<div class="toolbar">
		<button command="show-modal" commandfor="upload-csv">Upload Order CSV</button>
		<dialog class="upload-form" id="upload-csv">
			<form method="dialog" onsubmit={uploadCSV}>
				<h1>Upload Order CSV</h1>
				<input type="file" bind:files accept=".csv" />
				<button type="submit" disabled={!files || files?.length === 0}>Upload</button>
			</form>
		</dialog>
	</div>
	<h1>Orders ({totalOrderCount ?? 'None'}):</h1>
	{#if fetchStatusMessage}
		<div class="error-status">
			<div>Error fetching historical orders: {fetchStatusMessage}</div>
		</div>
	{/if}
	{#if countStatusMessage}
		<div class="error-status">
			<div>Error fetching total order count: {countStatusMessage}</div>
		</div>
	{/if}
	{#if wsStatusMessage || !connected}
		<div class="error-status">
			<div>Error loading live orders:</div>
			<div>Currently not connected to the backend servers. {wsStatusMessage}</div>
		</div>
	{/if}
	<div class="orders">
		{#each recentOrders as order (order.id)}
			{@const created_time = order.created_at ? new Date(order.created_at) : null}
			{@const updated_time = order.updated_at ? new Date(order.updated_at) : null}
			{@const scheduled_time = order.scheduled_for ? new Date(order.scheduled_for) : null}
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
							<div class="status {status}">{status}</div>
							<span>{item.name}</span>
							<span>{item.price ? '$' + item.price : ''}</span>
						</div>
					{/each}
				</div>
			</div>
		{:else}
			<p>No orders</p>
		{/each}
	</div>
	<div class="count_footer">{recentOrders.length} of {totalOrderCount}</div>
</div>

<style>
	.content {
		display: flex;
		box-sizing: border-box;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
		height: 100vh;

		h1 {
			margin: 0;
		}
	}

	.toolbar {
		display: flex;
		flex-grow: 1;
		max-height: fit-content;
		flex-direction: row;
		justify-content: right;
		align-items: center;
		gap: 1rem;
	}

	:modal.upload-form {
		border-width: 1px;

		&::backdrop {
			background-color: rgba(0, 0, 0, 0.4);
		}

		form {
			display: flex;
			flex-direction: column;
			gap: 1rem;

			button {
				background-color: teal;
				color: white;
				border: none;
				padding: 0.5rem 0.75rem;
				border-radius: 9999px;

				&:disabled {
					opacity: 60%;
					cursor: not-allowed;
				}
			}
		}
	}

	.error-status {
		display: flex;
		flex-direction: column;
		border: 1px solid red;
		padding: 0.5em;
		border-radius: 0.25em;
		color: red;
		gap: 0.25rem;
		background: rgba(255, 0, 0, 20%);

		:first-child {
			font-weight: bold;
		}

		:last-child {
			font-style: oblique;
		}
	}

	.orders {
		display: flex;
		flex-direction: column;
		border: 1px solid black;
		padding: 1em;
		border-radius: 0.5em;
		gap: 0.25em;
		overflow-y: scroll;
		flex-grow: 1;
	}

	.orders .order {
		background: lightgray;
		border: 1px solid grey;
		border-radius: 0.25em;
		padding: 0.5em;
		font-family: monospace;
		font-weight: 600;

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
