
function startSocket() {
    var ws = new WebSocket("ws://127.0.0.1:5678/")

    ws.onmessage = function (event) {
        data.push( -1 * (float(event.data))) // Negatives will wick up in the graph.
    };
}