// TODO: make pretty

class FeedbackForm {

  constructor(screenshooter) {
    this.screenshooter = screenshooter;
    this.$lip = this.makeLip();
    this.$modal = this.makeModal();
    this.resetModal();
    this.screenshot = null;
    this.hide();
    this.listen();
  }

  listen() {
    $('.feedback-lip-button').on('click', this.show.bind(this));
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
    this.$modal.find('.feedback-current-screenshot').html('').append(canvas);
  }

  hide() {
    this.$modal.modal('hide');
    return false;
  }

  show() {
    this.$modal.modal('show');
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
    if (!this.screenshot && !text) {
      alert("Enter a description or take a screenshot.");
      return;
    }
    this.$modal.find('.feedback-submit-button').text('Submitting...').prop('disabled', true);
    $.ajax({
      url: '/submit-feedback/',
      method: 'POST',
      data: {
        arxivId: arxivId,
        jpgData: jpgData,
        text: text,
      }
    }).then((ret) => {
      this.$modal.find('.modal-body').html(`Issue has been reported! <a href="${ret.issue_url}" target="_blank">Follow it on GitHub.</a>`);
      this.$modal.find('.feedback-submit-button').remove();
      this.$modal.on('hidden.bs.modal', () => {
        this.resetModal();
      });
    }).fail((xhr, error) => {
      alert(error);
    });
  }

  makeLip() {
    const $a = $('<button class="feedback-lip-button btn btn-primary" data-toggle="modal" data-target="#feedbackModal">Report a bug</button>');
    $('body').append($a);
    return $a;
  }

  makeModal() {
    $('#feedbackModal').remove();
    const $modal = $(`
      <div class="modal fade" id="feedbackModal" tabindex="-1" role="dialog" aria-labelledby="feedbackModalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
          <div class="modal-content">
          </div>
        </div>
      </div>
    `);

    $('body').append($modal);
    return $modal;
  }

  resetModal() {
    this.$modal.find('.modal-content').html(`
      <div class="modal-header">
        <h5 class="modal-title">Report a bug</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label for="feedback-text">Describe the issue</label>
          <textarea id="feedback-text" class="form-control" rows="5"></textarea>
        </div>

        <p>You can also attach a screenshot, if you like.</p>
        <p><button class="btn btn-secondary feedback-screenshot-button">Take screenshot</button></p>
        <p class="feedback-current-screenshot"></p>
        <p>This feature doesn't work on some browsers. If you just see a blank square, please describe the issue in the text box above.</p>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
        <button type="button" class="btn btn-primary feedback-submit-button">Submit</button>
      </div>
    `);
    this.$modal.find('.feedback-screenshot-button').on('click', this.takeScreenshot.bind(this));
    this.$modal.find('.feedback-submit-button').on('click', this.submit.bind(this));
  }

}


class Screenshooter {

  constructor() {
    this.state = Screenshooter.INACTIVE;
    this.onComplete = null;
    this.listen();
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

    this.takeScreenshot({
      x: startX + window.scrollX,
      y: startY + window.scrollY,
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
    return html2canvas($('body')[0], options);
  }

}
Screenshooter.LISTENING = 'LISTENING';
Screenshooter.INACTIVE = 'INACTIVE';
Screenshooter.ACTIVE = 'ACTIVE';
Screenshooter.PROCESSING = 'PROCESSING';
