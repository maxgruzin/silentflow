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
        var audios = $(this).closest("ul").find("audio");
        for (var i = 0; i < audios.length; i++)
        {
            if (!audios[i].paused || audios[i].currentTime)
            {
                audios[i].pause();
                audios[i].currentTime = 0;
                $(audios[i]).closest("li").find(".btn-pause").addClass("hide");
                $(audios[i]).closest("li").find(".btn-play").removeClass("hide");
            }
        }

        $(this).closest("li").find("audio").get(0).play();
        $(this).addClass("hide");
        $(this).closest("li").find(".btn-pause").removeClass("hide");
    });

    $('#cover-container').on('click', '.btn-pause', function(){
        $(this).closest("li").find("audio").get(0).pause();
        $(this).addClass("hide");
        $(this).closest("li").find(".btn-play").removeClass("hide");
    });

    $('audio').on('ended', function(){
        $(this).closest("li").find("audio").get(0).pause();
        $(this).closest("li").find(".btn-pause").addClass("hide");
        $(this).closest("li").find(".btn-play").removeClass("hide");
        if($(this).closest("li").next().find("audio").get(0))
        {
            $(this).closest("li").next().find("audio").get(0).play();
            $(this).closest("li").next().find(".btn-pause").removeClass("hide");
            $(this).closest("li").next().find(".btn-play").addClass("hide");
        }

    });


}