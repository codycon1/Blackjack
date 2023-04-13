$(document).ready(function () {
    let socket = new WebSocket('ws://127.0.0.1:8000/singleplayer');

    function sendresp(data) {
        console.log(JSON.stringify(data));
        socket.send(JSON.stringify(data));
    }

    function clear() {
        $('#dealercards').empty();
        $('#playercards').empty();
        $('#buttondiv').empty();
    }

    let response = {
        "primary": {

        },
        "split": {

        },
    };
    console.log(response);

    $('#reset').bind("click", function () {
        response["primary"]["action"] = "reset";
        sendresp(response);
        clear();
    });
    $('#reload').bind("click", function(){
        location.reload();
    });
    // socket.onmessage = function (event) {
    //     clear();
    //     let data = JSON.parse(event.data);
    //     clear();
    //     $('#pot').text(data['pot']);
    //     $('#balance').text(data['balance']);
    //     if ('dealercards' in data) {
    //         for (let i = 0; i < data.dealercards.length; i++) {
    //             $('#dealercards').append(
    //                 '<div class="col-md-3"><img class="mx-auto bg-light m-2 rounded" src="' + data.dealercards[i].url + '">'
    //             );
    //         }
    //     }
    //     if ('primary' in data) {
    //         if ('playercards' in data) {
    //             for (let i = 0; i < data.playercards.length; i++) {
    //                 $('#playercards').append(
    //                     '<div class="col-md-3"><img class="mx-auto bg-light m-2 rounded" src="' + data.playercards[i].url + '">'
    //                 );
    //             }
    //         }
    //         let btndiv = $('#buttondiv');
    //         if ('signal' in data) {
    //             for (let i = 0; i < data.readysignal.length; i++) {
    //                 let signal = data.readysignal[i];
    //                 if (signal === "Bet") {
    //                     btndiv.append(
    //                         `
    //                                 <form id="betform">
    //                                 <input type="number" min="1" max="${data['balance']}" class="form-control" name="betamt" id="betamt">
    //                                 <button class="btn btn-primary btn-round m-2" id="bet">Bet</button>
    //                                 </form>
    //                                 `
    //                     );
    //                     $('#betform').submit(function (e) {
    //                         response['betamt'] = $('#betamt').val();
    //                         e.preventDefault();
    //                         console.log(response);
    //                         sendresp(response);
    //                     });
    //                 } else {
    //                     btndiv.append(
    //                         `<button class="btn btn-primary btn-round m-2" id="${signal}">${signal}</button>`
    //                     );
    //                     $('#' + signal).bind('click', function () {
    //                         response['action'] = signal;
    //                         sendresp(response);
    //                     });
    //                 }
    //             }
    //         }
    //     }
    //     if ('split' in data) {
    //         if ('playercards' in data) {
    //             for (let i = 0; i < data.playercards.length; i++) {
    //                 $('#splitcards').append(
    //                     '<div class="col-md-3"><img class="mx-auto bg-light m-2 rounded" src="' + data.playercards[i].url + '">'
    //                 );
    //             }
    //         }
    //         let btndiv = $('#splitbuttondiv');
    //         if ('signal' in data) {
    //             for (let i = 0; i < data.readysignal.length; i++) {
    //                 let signal = data.readysignal[i];
    //                 if (signal === "Bet") {
    //                     btndiv.append(
    //                         `
    //                                 <form id="splitbetform">
    //                                 <input type="number" min="1" max="${data['balance']}" class="form-control" name="betamt" id="splitbetamt">
    //                                 <button class="btn btn-primary btn-round m-2" id="splitbet">Bet</button>
    //                                 </form>
    //                                 `
    //                     );
    //                     $('#splitbetform').submit(function (e) {
    //                         response['betamt'] = $('#splitbetamt').val();
    //                         e.preventDefault();
    //                         console.log(response);
    //                         sendresp(response);
    //                     });
    //                 } else {
    //                     btndiv.append(
    //                         `<button class="btn btn-primary btn-round m-2" id="${signal}">${signal}</button>`
    //                     );
    //                     $('#' + signal).bind('click', function () {
    //                         response['action'] = signal;
    //                         sendresp(response);
    //                     });
    //                 }
    //             }
    //         }
    //     }
    //     if ('result' in data) {
    //         let endcon = $('#endcondition');
    //         if (data['result']) {
    //             alert("YOU WON");
    //             endcon.append(
    //                 `<h4>YOU WON</h4>`
    //             );
    //         } else {
    //             alert("YOU LOST");
    //             endcon.append(
    //                 `<h4>YOU LOST</h4>`
    //             );
    //         }
    //     }
    // };
});
