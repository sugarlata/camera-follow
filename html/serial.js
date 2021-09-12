
function openSerial(event) {
    serialSend('open');
}

function readySerial(event) {
    serialSend('ready');
}

function closeSerial(event) {
    serialSend('close');
}

function serialSend(action) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://" + ipHost + "/serial", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({
        "action": action
    }));
}

var ipHost = location.host