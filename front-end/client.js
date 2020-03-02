
function startSocket() {
    var ws = new WebSocket("ws://127.0.0.1:5678/")

    ws.onmessage = function (event) {
        let newData = event.data;
        // Negatives will wick up in graph.
        newData = -1 * (float(newData)); 
        newData *= dataMultiplier;
        // Pass for further processing.
        data.push(newData)
    };
}