ccc = {};
ccc.pages = [];
ccc.page = 1;
ccc.pageOffset = 0;

ccc.reconnect = function() {
    var ws = new WebSocket("ws://" + document.location.host + "/ws");
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
        console.log("message", name, data);
        if (name == "page") {
            data.forEach(function(page) {
                ccc.pages.push(page);
            });
            ccc.loadPage(ccc.pages.length-1);
        } else if (name == "cameras") {
            ccc.updateCameras(data);
        } else if (name == "titles") {
            ccc.updateTitles(data);
        } else if (name == "pages") {
            ccc.updatePages(data);
        } else if (name == "error") {
            ccc.updateError(data);
        } else {
            console.log(name, data);
        }
    };
    ccc.ws = ws;
};

ccc.init = function() {
    ccc.left = document.createElement("img");
    ccc.right = document.createElement("img");
    ccc.left.style.top = 0;
    ccc.left.style.left = 0;
    ccc.left.style.width = "50%";
    ccc.left.style.position = "absolute";
    ccc.right.style.width = "50%";
    ccc.right.style.top = 0;
    ccc.right.style.right = 0;
    ccc.right.style.position = "absolute";
    document.body.appendChild(ccc.left);
    document.body.appendChild(ccc.right);
    this.reconnect();
    document.body.addEventListener("keydown", function(event) {
        if (event.code == "Space") {
            $(".info").remove();
            ccc.capture(ccc.page);
            ccc.page = ccc.page + 2;
            event.preventDefault();
        } else if (event.code == "KeyT") {
            $("<div>").addClass("info").html("use SPACE to capture next page").appendTo(document.body);
        } else if (event.code == "KeyF") {
            ccc.flipCameras();
        } else if (event.code == "KeyR") {
            ccc.detectCameras();
        } else if (event.code == "KeyQ") {
            location.reload();
        } else if (event.code == "ArrowLeft") {
            var next = ccc.page - 4;
            if (next < 1) {
                next = ccc.pages.length - 1;
            }
            ccc.loadPage(next);
            ccc.page = next + 2;
        } else if (event.code == "ArrowRight") {
            var next = ccc.page;
            if (next > ccc.pages.length - 1) {
                next = 1;
            }
            ccc.loadPage(next);
            ccc.page = next + 2;
        } else {
            console.log("keydown", event);
        }
    });
};

ccc.post = function(event, data) {
    ccc.ws.send(JSON.stringify([event, data]));
};

ccc.capture = function(page) {
    this.post("capture", page);
};
ccc.setCameras = function(cameras) {
    this.post("cameras", cameras);
};
ccc.detectCameras = function() {
    $(".info").remove();
    $("#error").remove();
    this.post("detectcameras", "");
};
ccc.setTitle = function(title) {
    ccc.post("title", title);
    this.title = title;
    $(".menu").remove();
    $("#quickhelp").remove();
};
ccc.getPath = function() {
    return ccc.post("path", "");
};
ccc.updateError = function(error) {
    $("#error").remove();
    $("<div>").attr({
        "id": "error"
    }).html(error).appendTo(document.body);
    
};
ccc.updatePages = function(pages) {
    this.pages = pages;
    this.page = pages.length + 1;
    this.loadPage(pages.length - 1);
};

ccc.updateTitles = function(titles) {
    $menu = $("<div>").addClass("menu");
    $("<h1>").html("bookscanner").appendTo($menu);
    book_click = function(title){
        ccc.setTitle(title);
    };
    
    new_book_click = function(){
        title = prompt("Enter title");
        $("div")
            .addClass("info")
            .html("Press SPACE to capture first page")
            .appendTo(document.body);
        ccc.setTitle(title);
    };
    $new_book = $("<a>")
        .addClass("new-book")
        .html("create new book")
        .on({
            click: new_book_click.bind(window)
        });
    for(var i=0; i<titles.length; i++){
        console.log(titles[i]);
        //add row
        $("<div>")
            .addClass("row")
            .attr({"id":i})
            .appendTo($menu);
    }
    $menu.appendTo(document.body);
    for(var i=0; i<titles.length; i++){
    // add first element (title-button)
        $("<a>")
            .addClass("title")
        .html(titles[i])
        .on({
            click: book_click.bind(window,titles[i])}
           )
        .appendTo($(".row#"+i));
    // add second element (zip-download)
        $("<a>")
            .addClass("options")
        .attr({
            "href":"zip?title="+titles[i]
        })
        .html("[zip]")
        .appendTo($(".row#"+i));
    // add third element (delete-book)
    $("<a>")
            .html("[del]")
            .addClass("options")
        .attr({
            "href":"del?title="+titles[i]
        })
        .on({
            click:
            function () { return confirm ("Sure?");}}
           )
            .appendTo($(".row#"+i));
    }
    //add new-book button
    $new_book
        .appendTo(
            $("<div>")
                .addClass("row")
                .appendTo(".menu"));
};

ccc.loadPage = function(page) {
    pages = [];
    pages.push(this.pages[page-1]);
    pages.push(this.pages[page]);
    $(".pagenumber").remove();
    $("<div>").addClass("pagenumber").css({
        left:0, "text-align": "right",
    }).html(page + this.pageOffset).appendTo(document.body);
    $("<div>").addClass("pagenumber").css({
        right:0, "text-align": "left",
    }).html(page + 1 + this.pageOffset).appendTo(document.body);
    ccc.updateImages(pages);
};

ccc.updateImages = function(pages) {
    console.log("updateImages", pages);
    t = "?" + (+new Date());
    ccc.left.src = "/" + pages[0] + t;
    ccc.right.src = "/" + pages[1] + t;
    /*
    this.pages.push(pages[0]);
    this.pages.push(pages[1]);
    */
};
ccc.getCameraName = function(i) {
    var name, cameras = this.cameras;
    if (cameras[i]) {
        //name = cameras[i][0] +  ( + cameras[i][1].split(",").pop() + )';
        name = cameras[i][0] + " (" + cameras[i][2] + ")";
    } else {
        name = "camera missing";
    }
    return name;
};
ccc.updateCameras = function(cameras) {
    var i, name;
    ccc.cameras = cameras;
    $(".camera").remove();
    console.log("update cameras", cameras);

    $("<div>").addClass("camera").css({
        left:0, "text-align": "right",
    }).html(this.getCameraName(0)).appendTo(document.body);

    $("<div>").addClass("camera").css({
        right:0, "text-align": "left",
    }).html(this.getCameraName(1)).appendTo(document.body);
};
ccc.flipCameras = function() {
    this.setCameras([this.cameras[1], this.cameras[0]]);
};
