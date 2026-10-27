<script>
    import { FileUp } from '@lucide/svelte';

	/**
	 * @type {FileList | null | undefined}
	 */
	 let files = $state(null);

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
</script>

<button command="show-modal" commandfor="upload-csv"><FileUp />Upload Orders</button>
<dialog class="upload-form" id="upload-csv">
    <form method="dialog" onsubmit={uploadCSV}>
        <h1>Upload Orders</h1>
        <input type="file" bind:files accept=".csv" />
        <button type="submit" disabled={!files || files?.length === 0}>Upload</button>
    </form>
</dialog>

<style>
    :modal.upload-form {
		border: 2px solid var(--color-background);
        color: var(--color-background);
        border-radius: 0.75rem;

		&::backdrop {
			background-color: rgba(0, 0, 0, 0.4);
		}

		form {
			display: flex;
			flex-direction: column;
            justify-content: space-evenly;
			gap: 1rem;
            width: 100%;
            min-width: 20rem;
            min-height: 10rem;
            height: 100%;

            h1 {
                margin: 0;
            }

			button {
                width: 100%;
            }
		}
	}
</style>
