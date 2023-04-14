$(document).ready(function () {
        let socket = new WebSocket('ws://127.0.0.1:8000/singleplayer');

        function sendresp(data) {
            console.log("Out: " + JSON.stringify(data));
            socket.send(JSON.stringify(data));
            resetJSON();
        }

        let response = {
            "primary": {},
            "split": {},
        };

        function resetJSON() {
            response = {
                "primary": {},
                "split": {},
            };
        }

        function clear() {
            $('#pot').empty();
            $('#s_pot').empty();
            $('#balance').empty();
            $('#dealercards').empty();
            $('#playercards').empty();
            $('#buttondiv').empty();
            $('#splitcards').empty();
            $('#splitbuttondiv').empty();
        }

        // BUTTON BINDINGS FOR DEBUG PURPOSES
        $('#reset').bind("click", function () {
            response["primary"]["action"] = "reset";
            sendresp(response);
        });
        $('#nuke').bind("click", function () {
            response["primary"]["action"] = "nuke";
            sendresp(response);
        })
        $('#reload').bind("click", function () {
            location.reload();
        });
        $('#hit').bind("click", function () {
            response["primary"]["action"] = "hit";
            sendresp(response);
        });
        $('#split_hit').bind("click", function () {
            response["split"]["action"] = "hit";
            sendresp(response);
        });

        socket.onmessage = function (event) {
            clear();
            let data = JSON.parse(event.data);
            console.log("In: " + JSON.stringify(data))
            if (data["balance"]) {
                $('#balance').text(data['balance']);
            }
            if ('primary' in data) {
                if ('signal' in data['primary']) {
                    let primary_signal = data['primary']['signal'];
                    let btndiv = $('#buttondiv');
                    for (let i = 0; i < primary_signal.length; i++) {
                        if (primary_signal[i] === "Bet") {
                            btndiv.append(
                                `
                                <form id="betform">
                                <input type="number" min="1" max="${data['balance']}" class="form-control" name="betamt" id="betamt">
                                <button class="btn btn-primary btn-round m-2" id="bet">Bet</button>
                                </form>
                                `
                            );
                            $('#betform').submit(function (e) {
                                response['primary']['action'] = "bet " + ($('#betamt').val());
                                e.preventDefault();
                                console.log(response);
                                sendresp(response);
                            });
                        }
                        else{
                            let signal = primary_signal[i];
                            btndiv.append(
                                `<button class="btn btn-primary btn-round m-2" id="${signal}">${signal}</button>`
                            );
                            $('#' + signal).bind('click', function () {
                                response['action'] = signal;
                                sendresp(response);
                            });
                        }
                    }
                }

                if ('bet' in data['primary']) {
                    $('#pot').text(data['primary']['bet']);
                }
            }
            if('dealer_cards' in data){
                for (let i=0; i<data['dealer_cards'].length; i++){
                    $('#dealercards').append(
                        '<div class="col-md-3"><img class="mx-auto bg-light m-2 rounded" src="' + data.dealer_cards[i].url + '">'
                    );
                }
            }
        };

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
    }
)
;
