import { writable } from "svelte/store";

export const totalOrderCount = writable(0);
export const totalItemCount = writable(0);
export const totalDispatchEligibleCount = writable(0);

/**
 * @type {import('svelte/store').Writable<{ title: string, summary: string }[]>}
 */
export const errorList = writable([]);
