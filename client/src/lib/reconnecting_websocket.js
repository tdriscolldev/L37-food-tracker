/**
 *  Creates a reconnecting WebSocket
 * @param {string} url WebSocket endpoint to connect to
 * @returns
 */
export function create_reconnecting_ws(url) {
	const ws = new WebSocket(url);

	// TODO: Add reconnecting logic

	return ws;
}
