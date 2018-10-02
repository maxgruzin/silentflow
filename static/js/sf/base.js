
document.addEventListener('DOMContentLoaded', function() {

    var elems = document.querySelectorAll('.menu_button.fixed-action-btn');
    var instances = M.FloatingActionButton.init(elems, {
        direction: 'right',
        hoverEnabled: false
    });

});