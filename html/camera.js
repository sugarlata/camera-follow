
function cameraStartFollow(event) {
    cameraFollow('start');
}
function cameraStopFollow(event) {
    cameraFollow('stop');
}
function cameraFollow(action) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://" + ipHost + "/camera", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({
        "action": action
    }));
}

var ipHost = location.host;