
function moveUp(event) {
    moveSend('up');
}
function moveLeft(event) {
    moveSend('left');
}
function moveRight(event) {
    moveSend('right');
}
function slideLeft(event) {
    moveSend('slide_left');
}
function slideRight(event) {
    moveSend('slide_right');
}
function moveDown(event) {
    moveSend('down');
}
function moveReset(event) {
    moveSend('reset');
}
function setZero(event) {
    moveSend('zero');
}
function moveAll(event) {
    let pan = document.getElementById("panInput").value;
    let tilt = document.getElementById("tiltInput").value;
    let slide = document.getElementById("slideInput").value;

    if (pan == "") {
        pan = 0;
    }

    if (tilt == "") {
        tilt = 0;
    }
    if (slide == "") {
        slide = 0;
    }

    sendAll(pan, tilt, slide)
}

function moveSend(action) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://" + ipHost + "/move", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({
        "action": action
    }));
}

function sendAll(pan, tilt, slide) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://" + ipHost + "/move", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({
        "action": "moveAll",
        "pan": pan,
        "tilt": tilt,
        "slide": slide
    }));
}

var ipHost = location.host;