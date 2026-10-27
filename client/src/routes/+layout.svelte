<script>
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import {totalOrderCount, totalItemCount, errorList, totalDispatchEligibleCount} from '#lib/stores.js';
	import { create_reconnecting_ws } from '#lib/reconnecting_websocket.js';
	import CSVUpload from '#lib/csv_upload.svelte';
	import { Forward, House } from '@lucide/svelte';

	/** @type {{children: import('svelte').Snippet}} */
	let { children } = $props();

	/**
	 * @type {{ title: string, summary: string }}
	 */
	let fetchError = $state({
		"title": "Encountered an error fetching status & counts",
		"summary": "",
	});

	/**
	 * @type {{ title: string, summary: string }}
	 */
	let wsError = $state({
		"title": "Live status & counts encountered an error",
		"summary": "",
	});

	/**
	 * Load total order count
	 */
	 const fetchCount = async () => {
		try {
			const order_response = await fetch(`http://localhost:8000/api/db/orders/count`);
			if (!order_response.ok) {
				console.log(`Failed to fetch: ${order_response.status}`);
				fetchError.summary = order_response.statusText;
				return;
			}

			const order_result = await order_response.json();
			console.debug('Fetched order count: ', order_result);
			$totalOrderCount = order_result;

			const item_response = await fetch(`http://localhost:8000/api/db/items/count`);
			if (!item_response.ok) {
				console.log(`Failed to fetch: ${item_response.status}`);
				fetchError.summary = item_response.statusText;
				return;
			}

			const item_result = await item_response.json();
			console.debug('Fetched item count: ', item_result);
			$totalItemCount = item_result;

			const dispatch_eligible_response = await fetch(`http://localhost:8000/api/db/dispatch/count`);
			if (!dispatch_eligible_response.ok) {
				console.log(`Failed to fetch: ${dispatch_eligible_response.status}`);
				fetchError.summary = dispatch_eligible_response.statusText;
				return;
			}

			const dispatch_eligible_result = await dispatch_eligible_response.json();
			console.debug('Fetched dispatch eligible item count: ', dispatch_eligible_result);
			$totalDispatchEligibleCount = dispatch_eligible_result;
		} catch (/** @type {any} */ error) {
			console.error(error.message);
			fetchError.summary = error.message;
		}
	};

	onMount(() => {
		$errorList = [...$errorList, fetchError, wsError];

		// Fetch historical data
		fetchCount();

		// Create websocket for live updates
		const ws = create_reconnecting_ws('ws://localhost:8000/api/db/status/ws');
		ws.onerror = (event) => {
			wsError.summary = JSON.stringify(event)
		};
		ws.onopen = () => {
			console.log('Connected to live order updates');
			wsError.summary = "";
		};
		ws.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data);
				console.info('Received stats/count update for: ', data);
				$totalOrderCount = data.order_count;
				$totalItemCount = data.item_count;
				$totalDispatchEligibleCount = data.deployable_count;
			} catch (error) {
				console.error(`Failed to update order list: ${error}`);
			}
		};
		ws.onclose = () => {
			wsError.summary = "Websocket closed!";
		};

		return () => {
			ws.close();
			$errorList = $errorList.filter((item) => item != wsError && item != fetchError);
		};
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="structure">
	<div class="toolbar">
		<nav>
			<a href="/"><House/>Orders ({$totalOrderCount})</a>
			<a href="/items">Items ({$totalItemCount})</a>
			<a href="/dispatch"><Forward/>Dispatch ({$totalDispatchEligibleCount})</a>
		</nav>
		<div class="actions">
			<CSVUpload/>
		</div>
	</div>
	<div class="error-list">
		{#each $errorList as error}
			{#if error.summary}
				<div class="error-status">
					<div>{error.title}</div>
					<div>{error.summary}</div>
				</div>
			{/if}
		{/each}
	</div>
	<div class="content">
		{@render children()}
	</div>
</div>


<style>
	.structure {
		display: grid;
		grid-template-rows: auto auto 1fr;
		box-sizing: border-box;
		padding: 1rem;
		padding-bottom: 2rem;
		gap: 0.25rem;
		height: 100dvh;
		background-color: var(--color-background);
		color: var(--color-text);

		/* > * {
			border: 1px solid red;
		} */
	}

	.toolbar {
		display: flex;
		flex-grow: 1;
		min-height: fit-content;
		height: 3rem;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		border-bottom: 2px solid var(--color-primary);
		padding-bottom: 0.1rem;

		:global(svg) {
			display: flex;
			box-sizing: border-box;
			width: 1em;
			height: 1em;
		}
	}

	nav {
		display: flex;
		flex-direction: row;
		gap: 1rem;
		place-items: center;
		width: fit-content;
		height: 100%;
		box-sizing: border-box;

		a {
			background-color: var(--color-secondary);
			color: var(--color-primary);
			display: flex;
			padding: 0.25em 0.5em;
			height: fit-content;
			align-items: center;
			justify-content: center;
			box-sizing: border-box;
			border-radius: 0.25em;
			gap: 0.5em;

			font-size: 1.2rem;
			font-weight: 500;
			text-decoration: none;
		}
	}

	.actions {
		display: flex;
		height: 100%;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
	}

	.content {
		display: flex;
		box-sizing: border-box;
		flex-direction: column;
		gap: 1rem;
		height: 100%;
		min-height: 0;
	}

	.error-list {
		margin-top: 0.4rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		height: fit-content;
		width: 100%;
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
</style>
