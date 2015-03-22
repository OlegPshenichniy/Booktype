(function (win, jquery) {
  "use strict";
  
  var initiator;
  var pc;
  var currentBookID = location.href.split("-book-").pop().replace("/", "");
  var PeerConnection = window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
  var IceCandidate = window.mozRTCIceCandidate || window.RTCIceCandidate;
  var SessionDescription = window.mozRTCSessionDescription || window.RTCSessionDescription;
  // TODO create ws url in another way
  var ws = new WebSocket(location.href.replace("http", "ws").replace("/video/", "/wbsckt/").replace(":8080", ":8090"));
  navigator.getUserMedia = navigator.getUserMedia || navigator.mozGetUserMedia || navigator.webkitGetUserMedia;

  // using only for debug
  ws.onopen = function () {
    console.log("ws.onopen Connection sucessfull");
  };

  // add message handler to web socket
  ws.onmessage = function (event) {
    console.log("ws.onmessage");

    if (event.data === "magic_overload") {
      alert("Sorry, but this node is overloaded!");
      window.close();
    }
    if (event.data === "inviter") {
      initiator = false;
      initialize();
    }
    if (event.data === "invited") {
      initiator = true;
      initialize();
    }
  };

  function initialize() {
    var constraints = {
      audio: false,
      video: true
    };
    navigator.getUserMedia(constraints, success, fail);
  }

  function success(stream) {
    console.log("navigator.getUserMedia success");
    pc = new PeerConnection(null);

    if (stream) {
      pc.addStream(stream);
      $("#local").attachStream(stream);
    }

    pc.onaddstream = function (event) {
      $("#remote").attachStream(event.stream);
      logStreaming(true);
    };
    pc.onicecandidate = function (event) {
      if (event.candidate) {
        ws.send(JSON.stringify(event.candidate));
      }
    };
    ws.onmessage = function (event) {
      var signal = JSON.parse(event.data);
      if (signal.sdp) {
        if (initiator) {
          receiveAnswer(signal);
        } else {
          receiveOffer(signal);
        }
      } else if (signal.candidate) {
        pc.addIceCandidate(new IceCandidate(signal));
      }
    };

    if (initiator) {
      createOffer();
    } else {
      // send invitation and wait..
      // TODO mock this.interval();
      win.booktype.connect();
      win.booktype.sendToChannel("/video/" + currentBookID + "/", {
          "command": "video_invite",
          "video_node_link": location.href
        },
        function () {},
        function () {}
      );

      log("Waiting for guest connection...");
    }
    logStreaming(false);
  }

  function fail() {
    console.log("navigator.getUserMedia fail");

    $("#traceback").text(Array.prototype.join.call(arguments, " "));
    $("#traceback").attr("class", "bg-danger");
    console.error.apply(console, arguments);
  }

  function createOffer() {
    log("Creating offer. Please wait.");
    pc.createOffer(function (offer) {
      log("Success offer");
      pc.setLocalDescription(offer, function () {
        log("Sending to remote...");
        ws.send(JSON.stringify(offer));
      }, fail);
    }, fail);
  }

  function receiveOffer(offer) {
    log("Received offer.");
    pc.setRemoteDescription(new SessionDescription(offer), function () {
      log("Creating response");
      pc.createAnswer(function (answer) {
        log("Created response");
        pc.setLocalDescription(answer, function () {
          log("Sent response");
          ws.send(JSON.stringify(answer));
        }, fail);
      }, fail);
    }, fail);
  }

  function receiveAnswer(answer) {
    log("received answer");
    pc.setRemoteDescription(new SessionDescription(answer));
  }

  function log() {
    $("#traceback").text(Array.prototype.join.call(arguments, " "));
    console.log.apply(console, arguments);
  }

  function logStreaming(streaming) {
    $("#streaming").text(streaming ? "[streaming]" : "[..]");
  }

  jquery.fn.attachStream = function (stream) {
    this.each(function () {
      this.src = URL.createObjectURL(stream);
      this.play();
    });
  };

})(window, jQuery);