$(document).ready(function () {

    document.getElementById('search-form').addEventListener('submit', function (e) {
        e.preventDefault();
        delay(function() {
            searchAlbums(document.getElementById('song-query').value);
        }, 0);
    }, false);

    document.getElementById('song-query').addEventListener('keyup', function(e) {
        delay(function() {
            searchAlbums(document.getElementById('song-query').value);
        }, 500);
    }, false);

});

var delay = (function(){
    var timer = 0;
    return function(callback, ms){
        clearTimeout (timer);
        timer = setTimeout(callback, ms);
    };
})();

function searchAlbums(query) {
    query = query.trim();
    if (query === ''){
        return;
    }
    $.ajax({
        url: 'https://api.spotify.com/v1/search',
        data: {
            q: query,
            type: 'track',
            limit: 10
        },
        success: function (response) {

            parseSearchAlbumsTracks(response.tracks.items);
        }
    });
}

song_preview_template = Handlebars.compile(document.getElementById('song-preview-template').innerHTML);

function parseSearchAlbumsTracks(tracks) {
    var resultsObj = document.getElementById('song-results');
    if (tracks.length === 0) {
        resultsObj.innerText = "No songs were found :(";
        return;
    } else {
        resultsObj.innerHTML = "";
    }
    for (var i = 0; i < tracks.length; i++) {
        var li = document.createElement('li');
        var div = document.createElement('div');
        div.innerHTML = song_preview_template(tracks[i]);
        var song_elem = div.children[0];
        song_elem.addEventListener('click', songClickHandler, false);
        var button = document.createElement('button');
        button.innerText = "Select";
        $(button).addClass('btn btn-info');
        button.addEventListener('click', selectSongHandler(song_elem, li));
        li.appendChild(button);
        li.appendChild(div);
        resultsObj.appendChild(li);
    }
}

function selectSongHandler(song_elem, li) {
    return function() {
        $('#chosenSong').empty();
        $(song_elem).appendTo('#chosenSong');
        $(li).remove();
        $('#step1btn').attr('disabled', false);
    };
}

var current_song = null;

function songClickHandler(e) {
    e.preventDefault();
    var element = $(e.target).closest('.song-preview');
    var song_url = element.data('song-url');

    if (element.hasClass('playing')) {
        current_song.pause();
    } else {
        if (current_song) {
            current_song.pause();
        }
        current_song = new Audio(song_url);
        current_song.play();
        element.removeClass('paused');
        element.addClass('playing');
        var handler = function() {
            element.removeClass('playing');
            element.addClass('paused');
        };
        current_song.addEventListener('ended', handler);
        current_song.addEventListener('pause', handler);
    }
}
