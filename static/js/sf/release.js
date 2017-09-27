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
        console.log("button play clicked");
        var id = this.id;
        $(this).closest("li").find("audio").get(0).play();
//        audio = "#pause-" + this.id.split('-')[2];
//        $("btn-pause-993").css( "display", "inline !important" );
//        $(audio).prop("play");
    });


}