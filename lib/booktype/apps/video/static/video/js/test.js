(function (win, jquery) {
  "use strict";
  
  var pc;
  var PeerConnection = window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
  navigator.getUserMedia = navigator.getUserMedia || navigator.mozGetUserMedia || navigator.webkitGetUserMedia;

  (function () {
    navigator.getUserMedia({
      audio: true,
      video: true
    }, success, fail);
  })();

  function success(stream) {
    pc = new PeerConnection(null);
    if (stream) {
      pc.addStream(stream);
      jquery("#local").attachStream(stream);
    }
    jquery("#traceback").text("Success!");
    jquery("#traceback").addClass("label-success");
  }

  function fail() {
    console.log("navigator.getUserMedia fail");

    jquery("#traceback").text("Fail!");
    jquery("#traceback").addClass("label-danger");
  }

  jquery.fn.attachStream = function (stream) {
    this.each(function () {
      this.src = URL.createObjectURL(stream);
      this.play();
    });
  };

})(window, jQuery);