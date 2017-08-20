// TODO: make pretty

class FeedbackForm {

  constructor(screenshooter) {
    this.screenshooter = screenshooter;
    this.$lip = this.makeLip();
    this.$div = this.makeForm();
    this.screenshot = null;
    this.hide();
  }

  listen() {
    $('#feedback-lip').on('click', this.show.bind(this));
    $('#feedback-screenshot').on('click', this.takeScreenshot.bind(this));
    $('#feedback-submit').on('click', this.submit.bind(this));
    $('#feedback-close').on('click', this.hide.bind(this));
  }

  takeScreenshot() {
    this.hide();
    this.screenshooter.onComplete = (canvas) => {
      this.show();
      this.setScreenshot(canvas);
    };
    this.screenshooter.activate();
    return false;
  }

  setScreenshot(canvas) {
    this.screenshot = canvas;
    $('#feedback-current-screenshot').html('').append(canvas);
  }

  hide() {
    this.$div.hide();
    return false;
  }

  show() {
    this.$div.show();
    return false;
  }

  submit() {
    const arxivId = window.location.pathname.split('/')[2];
    const url = '/submit-feedback/';
    var jpgData = this.screenshot
        ? this.screenshot
              .toDataURL("image/jpeg", 0.7)
              .replace('data:image/jpeg;base64,', '')
        : null;
    const text = $('#feedback-text').val();
    $.ajax({
      url: '/submit-feedback/',
      method: 'POST',
      data: {
        arxivId: arxivId,
        jpgData: jpgData,
        text: text,
      }
    }).then((ret) => {
      this.hide();
      alert('Follow the issue at ' + ret.issue_url);
    }).fail((xhr, error) => {
      this.hide();
      alert(error);
    });
  }

  makeLip() {
    const $a = $('<a href="#">Report a bug</a>');
    $a.attr('id', 'feedback-lip');
    $('body').append($a);
    return $a;
  }

  makeForm() {
    const $div = $(`
<div id="feedback-form">
<a href="#" id="feedback-close" title="Close">X</a>
<center>
<h3>Report a bug</h3>
<p><a id="feedback-screenshot" href="#">Take screenshot</a></p>
<p id="feedback-current-screenshot"></p>
<p><label for="feedback-text">Describe the issue</label><br />
  <textarea id="feedback-text"></textarea></p>
<p><input type="submit" id="feedback-submit" value="Submit" /></p>
</center>
</div>
`);
    $('body').append($div);
    return $div;
  }

}


class Screenshooter {

  constructor() {
    this.state = Screenshooter.INACTIVE;
    this.onComplete = null;
  }

  listen() {
    $(window).on('mousedown', this.begin.bind(this));
    $(window).on('mouseup', this.end.bind(this));
    $(window).on('mousemove', this.move.bind(this));
  }

  activate() {
    $('body').css('cursor', 'crosshair');

    this.state = Screenshooter.LISTENING;
  }

  begin(e) {
    if (this.state != Screenshooter.LISTENING) {
      return;
    }

    this.state = Screenshooter.ACTIVE;

    this.startX = e.clientX;
    this.startY = e.clientY;

    $('#screenshot-rect').remove();
    this.$rect = $('<div></div>');
    this.$rect.attr('id', 'screenshot-rect');
    $('body').append(this.$rect);
    $('body').css('cursor', 'crosshair');

    return false;
  }

  move(e) {
    if (this.state != Screenshooter.ACTIVE) {
      return;
    }

    const [startX, endX, startY, endY] = this.corners(e);

    this.$rect.css({
      left: startX,
      top: startY,
      width: endX - startX,
      height: endY - startY
    });
  }

  end(e) {
    if (this.state != Screenshooter.ACTIVE) {
      return;
    }

    const [startX, endX, startY, endY] = this.corners(e);

    const width = endX - startX;
    const height = endY - startY;

    this.state = Screenshooter.PROCESSING;
    $('#screenshot-rect').addClass('processing');

    return this.takeScreenshot({
      x: startX,
      y: startY,
      width: width,
      height: height,
    })
      .then((canvas) => {
        this.deactivate();
        if (this.onComplete) {
          this.onComplete(canvas);
        }
      });

    return false;
  }

  deactivate() {
    $('#screenshot-rect').remove();
    this.$rect = null;
    $('body').css('cursor', 'default');
    this.state = Screenshooter.INACTIVE;
  }

  corners(e) {
    var startX, endX, startY, endY;
    if (this.startX < e.clientX) {
      startX = this.startX;
      endX = e.clientX;
    } else {
      startX = e.clientX;
      endX = this.startX;
    }
    if (this.startY < e.clientY) {
      startY = this.startY;
      endY = e.clientY;
    } else {
      startY = e.clientY;
      endY = this.startY;
    }

    return [startX, endX, startY, endY];
  }

  saveScreenshot(canvas) {
    const $c = $(canvas);
    $('#screenshot').remove();
    $c.css('position', 'fixed');
    $c.css('border', '10px solid black');
    $c.attr('id', 'screenshot');
    $c.css({left: 50, top: 50});
    $('body').prepend($c);
  }

  takeScreenshot(options) {
    let cropper = document.createElement('canvas').getContext('2d');
    // save the passed width and height
    let finalWidth = options.width;
    let finalHeight = options.height;

    // update the options value so we can pass it to h2c
    options.width = finalWidth + options.x + 100;
    options.height = finalHeight + options.y + 100;

    return new Promise((resolve, reject) => {
      options.onrendered = (canvas) => {
        // do our cropping
        cropper.canvas.width = finalWidth;
        cropper.canvas.height = finalHeight;
        cropper.drawImage(canvas, -options.x, -options.y);
        resolve(cropper.canvas);
      }
      html2canvas($('body')[0], options);
    });
  }

}
Screenshooter.LISTENING = 'LISTENING';
Screenshooter.INACTIVE = 'INACTIVE';
Screenshooter.ACTIVE = 'ACTIVE';
Screenshooter.PROCESSING = 'PROCESSING';
