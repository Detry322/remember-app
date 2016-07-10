$(document).ready(function() {
  var opts = {
    lines: 13,
    length: 28,
    width: 14,
    radius: 42,
    scale: 0.75,
    corners: 1,
    color: '#000',
    opacity: 0.25,
    rotate: 0,
    direction: 1,
    speed: 1,
    trail: 60,
    fps: 20,
    zIndex: 2e9,
    className: 'spinner',
    top: '50%',
    left: '50%',
    shadow: false,
    hwaccel: false,
    position: 'absolute'
  };
  var target = document.getElementById('processing-spinner');
  var spinner = new Spinner(opts).spin(target);

  $('#step2btn').click(function() {
    console.log("Beginning submit");
    var data = {
      song: $('#chosenSong .song-preview').data('song-url'),
      video_clips: window.getVideoRanges()
    };
    $.ajax({
      type: "POST",
      url: '/create',
      data: JSON.stringify(data),
      contentType :'application/json',
      success: function(result) {
        $('#finalVideo video').get(0).src = result;
        var $active = $('.wizard .nav-tabs li.active');
        $active.next().removeClass('disabled');
        nextTab($active);
      },
      error: function() {
        alert("Sad error :(");
      }
    });
  });
});
