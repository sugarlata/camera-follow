// Initialization
var ipHost = location.host

// Socket Setup
var socket = new WebSocket('ws://' + ipHost + '/control');
socket.onmessage = function(evt) {
    try {
        message = JSON.parse(evt.data);
        if (message.responseType == 'log') {
            getLoggingResponse(message);
        }

    } catch (err) {
        console.log('Issue parsing response from server');
    }
}



// Send on Socket
function sendSocketData(data){
    socket.send(JSON.stringify(data));
}

// -------------------------------------------------------------------------
// Serial Functions

function openSerial(event) {
    const data = {
        'module': 'serial',
        'action': 'open'
    }
    sendSocketData(data);
}

function readySerial(event) {
    const data = {
        'module': 'serial',
        'action': 'ready'
    }
    sendSocketData(data);
}

function closeSerial(event) {
    const data = {
        'module': 'serial',
        'action': 'close'
    }
    sendSocketData(data);
}

// -------------------------------------------------------------------------
// PTS Functions

function ptsStartFollow(event) {
    const data = {
        'module': 'pt-move',
        'action': 'follow',
        'detail': 'enable'
    }
    sendSocketData(data);
}

function ptsStopFollow(event) {
    const data = {
        'module': 'pt-move',
        'action': 'follow',
        'detail': 'disable'
    }
    sendSocketData(data);
}

function ptsSend(pts, direction) {
    const data = {
        'module': 'pt-move',
        'action': 'move',
        'detail': {
            'pts': pts,
            'direction': direction
        }
    }
    sendSocketData(data);
}

function tiltUp(event) {
    ptsSend('tilt', 'up');
}

function tiltDown(event) {
    ptsSend('tilt', 'down');
}

function panLeft(event) {
    ptsSend('pan', 'left');
}

function panRight(event) {
    ptsSend('pan', 'right');
}

function slideLeft(event) {
    ptsSend('slide', 'left');
}

function slideRight(event) {
    ptsSend('slide', 'right');
}

function moveOrigin(event) {
    ptsSend('all', 'origin');
}

function resetPosition(event){
    
    const data = {
        'module': 'pt-move',
        'action': 'move-origin',
        'detail': {
            'pts': 'all'
        }
    }
    
    sendSocketData(data);
}

function ptsSet(event) {
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

    const data = {
        'module': 'pt-move',
        'action': 'move-all',
        'detail': {
            'pan': pan,
            'tilt': tilt,
            'slide': slide
        }
    }

    sendSocketData(data);
}

// -------------------------------------------------------------------------
// Object Tracking Functions

function objTrackStart(event) {
    const data = {
        'module': 'obj-track',
        'action': true
    }
    sendSocketData(data);
}
function objTrackStop(event) {
    const data = {
        'module': 'obj-track',
        'action': false
    }
    sendSocketData(data);
}

// -------------------------------------------------------------------------
// Mouse Click Functions

function returnClickPos(event) {
    
    let element = document.getElementById('imageStream')
    let rect = element.getBoundingClientRect();

    if (rect.left <= event.clientX && event.clientX <= rect.right && rect.top <= event.clientY && event.clientY <= rect.bottom) {

        const data = {
            'module': 'click-position',
            'action': 'pos-update',
            'position': {
                'x': event.clientX - rect.left,
                'y': event.clientY - rect.top    
            }
        }
        sendSocketData(data);
    }
}

// -------------------------------------------------------------------------
// Camera Functions

function setInterval(event){

    let interval = 5;

    const data = {
        'module': 'camera',
        'action': 'set-interval',
        'detail': {
            'interval': interval
        }
    }

    sendSocketData(data);

}

function modifyInterval(event){

    let interval = 5;
    let modifyType = 'sinusoidal'

    const data = {
        'module': 'camera',
        'action': 'modify-interval',
        'detail': {
            'interval': interval,
            'modify-type': modifyType
        }
    }

    sendSocketData(data);

}

function startInterval(event){

    const data = {
        'module': 'camera',
        'action': 'start-interval'
    }

    sendSocketData(data);

}

function stopInterval(event){

    const data = {
        'module': 'camera',
        'action': 'stop-interval'
    }

    sendSocketData(data);

}

function takeShotImmediate(event){

    const data = {
        'module': 'camera',
        'action': 'take-shot'
    }

    sendSocketData(data);

}

// -------------------------------------------------------------------------
// Logging Response

function getLoggingResponse(data) {
    console.log(data);
}

// -------------------------------------------------------------------------
// Listeners

document.addEventListener("click", returnClickPos);