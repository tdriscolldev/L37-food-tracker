<script>
	import { onMount } from 'svelte';
	import { create_reconnecting_ws } from '#lib/reconnecting_websocket.js';
    import {totalOrderCount, errorList} from '#lib/stores.js';
	import Order from '#lib/order.svelte';

	const LIVE_PAGE_ORDER_MAX = 100;

	/**
	 * @type {Array<any>}
	 */
	let recentOrders = $state([]);

    /**
	 * @type {{ title: string, summary: string }}
	 */
	let fetchError = $state({
		"title": "Encountered an error fetching historical orders",
		"summary": "",
	});

    /**
	 * @type {{ title: string, summary: string }}
	 */
	let wsError = $state({
		"title": "Live orders encountered an error",
		"summary": "",
	});


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
			fetchError.summary = '';
			const response = await fetch(`http://localhost:8000/api/db/orders/recent?limit=${LIVE_PAGE_ORDER_MAX}`);
			if (!response.ok) {
				console.log(`Failed to fetch: ${response.status}`);
				fetchError.summary = response.statusText;
				return;
			}

			const result = await response.json();
			console.log('Fetched entries: ', result);
			recentOrders = result;
			filterOrders();
		} catch (/** @type {any} */ error) {
			console.error(error.message);
			fetchError.summary = error.message;
		}
	};

	onMount(() => {
        $errorList = [...$errorList, fetchError, wsError];

		// Fetch historical data
		fetchDB();

		// Create websocket for live updates
		const ws = create_reconnecting_ws('ws://localhost:8000/api/db/orders/ws');
		ws.onerror = (event) => {
			wsError.summary = `Error: ${JSON.stringify(event)}`;
		};
		ws.onopen = () => {
			console.log('Connected to live order updates');
			wsError.summary = '';
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
			} catch (error) {
				console.error(`Failed to update order list: ${error}`);
			}
		};
		ws.onclose = () => {
			wsError.summary = 'Websocket closed!';
		};

		return () => {
			ws.close();
            $errorList = $errorList.filter((item) => item != wsError && item != fetchError);
		};
	});
</script>

<div class="content">
	<div class="toolbar">
	</div>
	<h1>Recent Orders:</h1>
    <div class="count_footer">{recentOrders.length} of {$totalOrderCount}</div>
	<div class="orders">
		{#each recentOrders as order (order.id)}
			<Order order={order}/>
		{:else}
			<p>No orders</p>
		{/each}
	</div>
</div>

<style>
	.content {
		display: flex;
		box-sizing: border-box;
		flex-direction: column;
		gap: 1rem;
		height: 100%;

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

	.orders {
		display: flex;
		flex-direction: column;
		border: 1px solid black;
		padding: 1em;
		border-radius: 0.5em;
		gap: 0.75em;
		overflow-y: scroll;
		flex-grow: 1;
        background-color: var(--color-primary);
	}
</style>
