window.onload = function(){
    //player

    // associate functions with the 'onclick' events
//    play.onclick = playAudio;
//    pause.onclick = pauseAudio;
//
//    function playAudio() {
//        myAudio.play();
//    }
//
//    function pauseAudio() {
//        myAudio.pause();
//    }


    $('#cover-container').on('click', '.btn-play', function(){
        var id = this.id;
        $(this).closest("li").find("audio").get(0).play();
        $(this).addClass("hide");
        $(this).closest("li").find(".btn-pause").removeClass("hide");
    });

    $('#cover-container').on('click', '.btn-pause', function(){
        //var id = this.id;
        $(this).closest("li").find("audio").get(0).pause();
        $(this).addClass("hide");
        $(this).closest("li").find(".btn-play").removeClass("hide");
    });

    $('audio').on('ended', function(){
        $(this).closest("li").find("audio").get(0).pause();
        // $(this).addClass("hide");
        $(this).closest("li").find(".btn-pause").addClass("hide");
        $(this).closest("li").find(".btn-play").removeClass("hide");
    });


}