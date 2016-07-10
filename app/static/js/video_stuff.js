$(document).ready(function(){

  var video_elem = document.querySelector('#videoContainer video');
  var video = video_func(video_elem);

  var canvas_elem = document.getElementById('videoScrubber');
  var canvas = canvas_func(canvas_elem, video);

  video_elem.addEventListener('timeupdate', function(e) {
    click = e.target.currentTime/e.target.duration * canvas_elem.width;
    canvas.cursor = { x: click, y: 3 };
    canvas.redraw();
  });

  canvas_elem.addEventListener('mousemove', function(e) {
    canvas.cursor = { x: e.offsetX, y: e.offsetY };
    canvas.redraw();
    video.scrubToPercent(canvas.getCursorPercent());
  });

  canvas_elem.addEventListener('mousedown', function(e) {
    var percent = e.offsetX / canvas_elem.width;
    canvas.drag_start = new Date();
    if (video.insideAnyRange(percent)) return;
    canvas.dragging = { x: e.offsetX };
  });
  canvas_elem.addEventListener('mouseup', function(e) {
    if (!canvas.dragging) return;
    var start_percent = canvas.dragging.x / canvas_elem.width;
    var end_percent = e.offsetX / canvas_elem.width;
    var range = {
      start: start_percent * video_elem.duration,
      end: end_percent * video_elem.duration
    };
    var duration = Math.abs(end_percent - start_percent) * video_elem.duration;
    if (!video.rangeOverlapsRanges(range) && duration > 2 && duration < 12) {
      video.addRange(start_percent, end_percent);
    }
    canvas.dragging = false;
    canvas.redraw();
  });

  canvas_elem.addEventListener('click', function(e) {
    $('#lengthCheck').text((Math.round(10*video.totalRangeTime())/10) + ' seconds');
    checkVideoCompletion(video);
    if (new Date() - canvas.drag_start > 300) return;
    var percent = e.offsetX / canvas_elem.width;
    video.removeRangeForPercent(percent);
    checkVideoCompletion(video);
    $('#lengthCheck').text((Math.round(10*video.totalRangeTime())/10) + ' seconds');
    canvas.redraw();
  });
  //canvas_elem.addEventListener('click', canvas.registerClick);

  canvas_elem.addEventListener('mouseout', function() {
    if (!canvas.dragging)
      canvas.cursor = null;
    canvas.redraw();
  });
  canvas.cursor = null;
  canvas.dragging = false;
  video.current_file = null;
  setCanvasSize(canvas_elem);
  $(window).resize(function(){
    setCanvasSize(canvas_elem);
  });

  myDropzone = new Dropzone("div#videoDropzone", {
    acceptedFiles: "video/mp4,*.mp4",
    url: '/upload',
    previewTemplate: '<div style="display:none"></div>',
    accept: function(file, done) {
      addVideoFile(video, canvas, myDropzone, file);
      done();
    }
  });
  var playing = false;
  $(document).keydown(function(e) {
    if (e.which != 32) return;
    if (e.target.tagName.toLowerCase() == 'input') return;
    if (playing) {
      video.pause();
    } else {
      video.play();
    }
    playing = !playing;
    return false;
  });
  $('#step1btn').click(function() {
    setTimeout(function(){
      setCanvasSize(canvas_elem);
    }, 10);
  });


  window.getVideoRanges = function() {
    var mapping = video.getAllRanges();
    var result = {};
    for (var guid in mapping) {
      if (mapping.hasOwnProperty(guid)) {
        var filename = null;
        $('#uploadedVideos .video-preview').each(function(){
          if (guid == $(this).data('guid')) {
            filename = $(this).data('video-url');
          }
        });
        if (!filename) continue;
        var ranges = mapping[guid];
        result[filename] = [];
        for (var i = 0; i < ranges.length; i++) {
          var range = ranges[i];
          result[filename].push({
            start: (range.start < range.end) ? range.start : range.end,
            end: (range.start < range.end) ? range.end : range.start
          });
        }
      }
    }
    return result;
  };
});

video_preview_template = Handlebars.compile(document.getElementById('video-preview-template').innerHTML);

function guid() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
  }
  return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
    s4() + '-' + s4() + s4() + s4();
}

function addVideoFile(video, canvas, dropzone, file) {
  var li = document.createElement('li');
  var div = document.createElement('div');
  var friendlySize = dropzone.filesize(file.size);
  div.innerHTML = video_preview_template({ name: file.name, size: friendlySize });
  var elem = div.children[0];
  $(elem).data('guid', guid());
  li.appendChild(div);
  $('#uploadedVideos').append(li);
  div.addEventListener('click', function() {
    $('.video-preview').removeClass('selected');
    $(elem).addClass('selected');
    var guid = $(elem).data('guid');
    file.completed = false;
    video.setVideoFromFile(file, guid);
    video.current_file = guid;
    setTimeout(function() { canvas.redraw(); }, 100);
  });
  if ($('#uploadedVideos').get(0).children.length === 1) {
    $(div).click();
  }
  var upload_percent_obj = $(div).find('.uploaded-percent');
  dropzone.on('uploadprogress', function(f, percent) {
    if (f != file) return;
    upload_percent_obj.text((Math.floor(10*percent)/10) + '%');
  });
  dropzone.on('error', function(f) {
    if (f != file) return;
    upload_percent_obj.text('An error occured :(, please try again');
    $(elem).addClass('error');
    setTimeout(function() {
      video.getAllRanges()[guid] = [];
      $(li).fadeOut();
    }, 3000);
  });
  dropzone.on('complete', function(f) {
    if (f != file) return;
    if (upload_percent_obj.text().indexOf('error') == -1) {
      upload_percent_obj.text('Done!');
      checkVideoCompletion(video);
      $(elem).data('video-url', f.xhr.response);
    }
  });
}

function checkVideoCompletion(video) {
  var completed = true;
  $('#uploadedVideos .video-preview .uploaded-percent').each(function() {
    if ($(this).text().indexOf('Done') < 0) {
      completed = false;
    }
  });

  if (!completed || video.totalRangeTime() <= 45) {
    $('#step2btn').attr('disabled', true);
  } else {
    $('#step2btn').attr('disabled', false);
  }
}

function setCanvasSize(canvas) {
  canvas.setAttribute('width', canvas.clientWidth);
  canvas.setAttribute('height', canvas.clientHeight);
}

var video_func = (function(video){
  var videoguid_to_ranges = {};
  return {
    scrubToPercent: function(percent) {
      var location = video.duration * percent;
      if (isNaN(location)) return;
      video.currentTime = location;
    },
    setVideoFromFile: function(file, guid) {
      var src = URL.createObjectURL(file);
      video.src = src;
      if (!(guid in videoguid_to_ranges)) {
        videoguid_to_ranges[guid] = [];
      }
    },
    pause: function() {
      video.pause();
    },
    play: function() {
      video.play();
    },
    rangeOverlapsRanges: function(range) {
      var ranges = videoguid_to_ranges[this.current_file];
      var range_start = (range.start < range.end) ? range.start : range.end;
      var range_end = (range.start < range.end) ? range.end : range.start;
      if (!ranges) return true;
      for (var i = 0; i < ranges.length; i++) {
        var other = ranges[i];
        var other_start = (other.start < other.end) ? other.start : other.end;
        var other_end = (other.start < other.end) ? other.end : other.start;
        if (Math.max(range_start,other_start) <= Math.min(range_end,other_end))
          return true;
      }
      return false;
    },
    insideRange: function(percent, range) {
      var time = percent * video.duration;
      var start = range.start;
      var end = range.end;
      if (start < end) {
        return (start < time && time < end);
      } else {
        return (end < time && time < start);
      }
    },
    insideAnyRange: function(percent) {
      var ranges = videoguid_to_ranges[this.current_file];
      if (!ranges) return true;
      for (var i = 0; i < ranges.length; i++) {
        if (this.insideRange(percent, ranges[i])) {
          return true;
        }
      }
      return false;
    },
    addRange: function(start, end) {
      if (this.current_file === null) return;

      var start_t = video.duration * start;
      var end_t = video.duration * end;

      videoguid_to_ranges[this.current_file].push({
        start: start_t,
        end: end_t
      });
    },
    removeRangeForPercent: function(percent) {
      var result = [];
      var ranges = videoguid_to_ranges[this.current_file];
      if (!ranges) return;
      for (var i = 0; i < ranges.length; i++) {
        if (this.insideRange(percent, ranges[i])) continue;
        result.push(ranges[i]);
      }
      videoguid_to_ranges[this.current_file] = result;
    },
    getPercentRanges: function() {
      if (this.current_file === null) return [];

      var result = [];
      var ranges = videoguid_to_ranges[this.current_file];
      for (var i = 0; i < ranges.length; i++) {
        result.push({
          start: ranges[i].start / video.duration,
          end: ranges[i].end / video.duration
        });
      }

      return result;
    },
    getAllRanges: function() {
      return videoguid_to_ranges;
    },
    totalRangeTime: function() {
      var total = 0;
      for (var key in videoguid_to_ranges) {
        if (videoguid_to_ranges.hasOwnProperty(key)) {
          var ranges = videoguid_to_ranges[key];
          for (var i = 0; i < ranges.length; i++) {
            total += Math.abs(ranges[i].start - ranges[i].end);
          }
        }
      }
      return total;
    },
    element: video
  };
});

var canvas_func = (function(canvas, video){
  var ctx = canvas.getContext("2d");
  return {
    clear: function() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    },
    getCursorPercent: function() {
      if (this.cursor === null)
        return 0;
      return this.cursor.x / canvas.width;
    },
    fillBox: function(x, y, width, height, color) {
      var old_color = ctx.fillStyle;
      if (color != old_color)
        ctx.fillStyle = color;
      ctx.fillRect(x, y, width, height);
      if (color != old_color)
        ctx.fillStyle = old_color;
    },
    drawVertical: function(x) {
      this.fillBox(x, 0, 1, canvas.height, '#000000');
    },
    drawCursor: function() {
      if (this.cursor !== null) {
        this.drawVertical(this.cursor.x);
      }
    },
    drawDrag: function() {
      if (!this.dragging) return;
      this.fillBox(this.dragging.x, 0, this.cursor.x - this.dragging.x, canvas.height, '#99CC99');
      this.drawVertical(this.dragging.x);
      var text = (Math.floor(Math.abs(this.cursor.x - this.dragging.x) * 10 / canvas.width * video.element.duration) / 10) + ' seconds';
      ctx.fillText(text, this.cursor.x + 4, canvas.height / 2 + 2);
    },
    drawRanges: function() {
      var ranges = video.getPercentRanges();
      for (var i = 0; i < ranges.length; i++) {
        var start_p = ranges[i].start * canvas.width;
        var end_p = ranges[i].end * canvas.width;
        this.fillBox(start_p, 0, end_p - start_p, canvas.height, '#AACCAA');
        this.drawVertical(start_p);
        this.drawVertical(end_p);
      }
    },
    redraw: function() {
      this.clear();
      this.drawDrag();
      this.drawRanges();
      this.drawCursor();
    }
  };
});
