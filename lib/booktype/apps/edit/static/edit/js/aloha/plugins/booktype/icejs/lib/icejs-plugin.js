define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'aloha/ephemera', 'booktype'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Ephemera, booktype) {
    return Plugin.create('icejs', {
      init: function () {

        var _initIceTracker = function (elementId) {
          var text = document.getElementById(elementId);
          window.tracker = new ice.InlineChangeEditor({
            element: text,
            handleEvents: true,
            currentUser: {id: win.booktype.username, name: win.booktype.username},
            plugins: [
              'IceAddTitlePlugin',
              {
                name: 'IceCopyPastePlugin',
                settings: {
                  pasteType: 'formattedClean',
                  preserve: 'p,a[href],i,em,b,span,ul,ol,li,hr'
                }
              }
            ]
          }).startTracking();
        };

        var _destroyIceTracker = function () {
          window.tracker.stopTracking();
          delete window.tracker;
        };

        // add button handler
        UI.adopt('icejs', null, {
          click: function () {
            var body = document.getElementById('contenteditor');
            if (jQuery(body).hasClass('CT-hide')) {
              jQuery(body).removeClass('CT-hide');
            } else {
              jQuery(body).addClass('CT-hide');
            }
          }
        });

        // add aloha destro
        Aloha.bind('aloha-editable-destroyed', function ($event, editable) {
          _destroyIceTracker();
        });

        //Aloha.bind('aloha-editable-created', function ($event, editable) {
        //  _initIceTracker('contenteditor');
        //});
      }
    });
  });