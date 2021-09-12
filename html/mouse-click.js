
function returnMousePos(event) {

    let element = document.getElementById('imageStream')
    let rect = element.getBoundingClientRect();

    if (rect.left <= event.clientX && event.clientX <= rect.right && rect.top <= event.clientY && event.clientY <= rect.bottom) {

        var xhr = new XMLHttpRequest();
        xhr.open("POST", "http://" + ip + "/image-click", true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify({
            "x": event.clientX - rect.left,
            "y": event.clientY - rect.top
        }));

    }
  }
  
  var ip = location.host
  document.addEventListener("click", returnMousePos);
