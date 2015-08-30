define(
  ['jquery'],
  function (jQuery) {
    "use strict";

    function squareSelector(container) {
      /**
       Square table size selector.
       :Args:
       - container: container for table
       */

      var $this = this;

      this.container = container;
      this.table = null;
      this._x = null;
      this._y = null;

      // hooks. called with next agruments: item, x, y
      this.onHighlight = null;
      this.onSelect = null;

      this.draw = function (x, y) {
        $this._x = x;
        $this._y = y;

        $this.table = jQuery('<table class="square-selector"></table>');
        $this.span = jQuery('<span class="square-selector-indicate"></span>');

        $this.container.html('');
        $this.container.append($this.table);
        $this.container.append($this.span);

        for (var _y = 1; _y <= y; _y++) {
          var tr = jQuery('<tr></tr>');
          for (var _x = 1; _x <= x; _x++) {
            var td = jQuery('<td></td>');
            td.attr('id', 'square-selector-item-' + _x + '-' + _y);
            td.hover($this._itemOnHover);
            td.click($this._itemOnClick);
            tr.append(td);
          }
          $this.table.append(tr)
        }
      };

      this.highlightArea = function (x, y) {
        $this.table.find('td').removeClass('selected');
        for (var _x = 1; _x <= x; _x++) {
          for (var _y = 1; _y <= y; _y++) {
            jQuery('#square-selector-item-' + _x + '-' + _y).addClass('selected');
          }
        }
        $this._showSize(x, y);
      };

      this._itemOnHover = function (item) {

        var _id = item.currentTarget.getAttribute('id');
        _id = _id.split('-');
        var x = Number(_id[3]);
        var y = Number(_id[4]);

        if (x === $this._x && x < 20) {
          $this.draw($this._x + 1, $this._y);
        } else if (y === $this._y && y < 20) {
          $this.draw($this._x, $this._y + 1);
        }
        $this.highlightArea(x, y);

        // execute hook
        if ($this.onHighlight) {
          $this.onHighlight(item, x, y);
        }
      };

      this._itemOnClick = function (item) {
        var _id = item.currentTarget.getAttribute('id');
        _id = _id.split('-');
        var x = Number(_id[3]);
        var y = Number(_id[4]);

        // execute hook
        if ($this.onSelect) {
          $this.onSelect(item, x, y);
        }
      };

      this._showSize = function (x, y) {
        $this.span.html(x + ' X ' + y);
      };

    }

    return {'squareSelector': squareSelector}
  }
);
