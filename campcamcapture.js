ccc = {};
ccc.page = 1;

ccc.reconnect = function() {
    var ws = new WebSocket('ws://' + document.location.host + '/ws');
    ws.onopen = function(event) {
        //
    };
    ws.onerror = function(event) {
        ws.close();
    };
    ws.onclose = function(event) {
        setTimeout(ccc.reconnect, 500);
    };
    ws.onmessage = function(event) {
        var name, data = JSON.parse(event.data);
        name = data[0];
        data = data[1];
        console.log('message', name, data);
        if (name == 'page') {
            ccc.updateImages(data);
        } else if (name == 'cameras') {
            ccc.updateCameras(data);
        } else {
            console.log(name, data);
        }
    };
    ccc.ws = ws;
};

ccc.init = function() {
    ccc.left = document.createElement('img');
    ccc.right = document.createElement('img');
    ccc.left.style.top = 0;
    ccc.left.style.left = 0;
    ccc.left.style.width = '50%';
    ccc.left.style.position = 'absolute';
    ccc.right.style.width = '50%';
    ccc.right.style.top = 0;
    ccc.right.style.right = 0;
    ccc.right.style.position = 'absolute';
    document.body.appendChild(ccc.left);
    document.body.appendChild(ccc.right);
    this.reconnect();
    document.body.addEventListener("keypress", function(event) {
        if (event.code == 'KeyT') {
            ccc.capture(ccc.page);
            ccc.page++
        } else if (event.code == 'KeyF') {
            ccc.flipCameras();
        } else {
            console.log('keypress', event);
        }
    });

};

ccc.post = function(event, data) {
    ccc.ws.send(JSON.stringify([event, data]));
};

ccc.capture = function(page) {
    this.post('capture', page);
};
ccc.setCameras = function(cameras) {
    this.post('cameras', cameras);
};

ccc.updateImages = function(page) {
    var left = '/scan/' + page + '_left.jpg';
    var right = '/scan/' + page + '_right.jpg';
    console.log('updateImages', left, right);
    ccc.left.src = left;
    ccc.right.src = right;

};
ccc.updateCameras = function(cameras) {
    ccc.cameras = cameras;
    console.log('updateCameras', cameras);
};
ccc.flipCameras = function() {
    this.setCameras([this.cameras[1]. this.cameras[0]]);
};
