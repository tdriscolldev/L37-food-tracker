<script>
	import { onMount } from 'svelte';
	import { create_reconnecting_ws } from '#lib/reconnecting_websocket.js';
    import {totalDispatchEligibleCount, errorList} from '#lib/stores.js';
	import Item from '#lib/item.svelte';

	const LIVE_PAGE_ITEM_MAX = 100;

	/**
	 * @type {Array<any>}
	 */
	let recentItems = $state([]);

    /**
	 * @type {{ title: string, summary: string }}
	 */
	let fetchError = $state({
		"title": "Encountered an error fetching historical items",
		"summary": "",
	});

    /**
	 * @type {{ title: string, summary: string }}
	 */
	let wsError = $state({
		"title": "Live items encountered an error",
		"summary": "",
	});


	const filterItems = () => {
		// Trim back to max limit
		recentItems = recentItems
			.sort((a, b) => Date.parse(b.history.at(-1).time) - Date.parse(a.history.at(-1).time))
            .filter((a) => !["with_courier", "delivered", "canceled"].includes(a.history.at(-1).status))
			.slice(0, LIVE_PAGE_ITEM_MAX);
	};

	/**
	 * Load historical item data
	 */
	const fetchDB = async () => {
		try {
			fetchError.summary = '';
			const response = await fetch(`http://localhost:8000/api/db/dispatch?limit=${LIVE_PAGE_ITEM_MAX}`);
			if (!response.ok) {
				console.log(`Failed to fetch: ${response.status}`);
				fetchError.summary = response.statusText;
				return;
			}

			const result = await response.json();
			console.log('Fetched entries: ', result);
			recentItems = result;
			filterItems();
		} catch (/** @type {any} */ error) {
			console.error(error.message);
			fetchError.summary = error.message;
		}
	};

    /**
     * Make a POST request to mark item as dispatched
     * @param item_id {number}
     */
    const markDispatched = async (item_id) => {
        try {
			const response = await fetch(`http://localhost:8000/api/db/items/${item_id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    "status": "dispatched",
                })
            });
			if (!response.ok) {
				console.log(`Failed to dispatch: ${response.status}`);
				return;
			}
		} catch (/** @type {any} */ error) {
			console.error(error.message);
		}
    }

	onMount(() => {
        $errorList = [...$errorList, fetchError, wsError];

		// Fetch historical data
		fetchDB();

		// Create websocket for live updates
		const ws = create_reconnecting_ws('ws://localhost:8000/api/db/items/ws');
		ws.onerror = (event) => {
			wsError.summary = `Error: ${JSON.stringify(event)}`;
		};
		ws.onopen = () => {
			console.log('Connected to live item updates');
			wsError.summary = '';
		};
		ws.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data);
				console.debug('Received update for: ', data);

				let index = recentItems.findIndex((item) => item.id == data.id);
				// Replace item in list
				if (index >= 0) {
					recentItems[index] = data;
				} else {
					// Append to list
					recentItems.push(data);
				}
				filterItems();
			} catch (error) {
				console.error(`Failed to update item list: ${error}`);
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
	<h1>Items to Dispatch</h1>
    <div class="count_footer">{recentItems.length} of {$totalDispatchEligibleCount}</div>
	<div class="items">
		{#each recentItems as item (item.id)}
            <div class="item-container">
			    <Item {item}/>
                <button onclick={() => markDispatched(item.id)}>Deploy</button>
            </div>
		{:else}
			<p>No items</p>
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

	.items {
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

    .item-container {
        display: flex;
        flex-direction: row;
        width: 100%;
        gap: 1rem;
        place-items: center;
        justify-content: right;
    }
</style>
