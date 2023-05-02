$(document).ready(function () {
        let socket = new WebSocket('ws://127.0.0.1:8000/multiplayer');
        console.log("Document ready")

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
                "ready_action": null,
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

        function clear_server_sync() {
            $('#players').empty();
            $('#mp_buttondiv').empty();
        }

        // BUTTON BINDINGS FOR DEBUG PURPOSES
        $('#reset').bind("click", function () {
            response["primary"]["action"] = "reset";
            sendresp(response);
        });
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

        socket.onopen = function () {
            console.log("Socket opened")
        }

        socket.onmessage = function (event) {
            let mp_sync = false;
            console.log("Receiving a message");
            console.log("Raw data: " + event.data);
            let data = JSON.parse(event.data);
            // data = JSON.parse(data); // The stupid thing is extra stringified so you have to call this twice
            console.log(data);
            if ('players' in data) {
                clear_server_sync()
                mp_sync = true;
                for (let i = 0; i < data['players'].length; i++) {
                    console.log(data['players'][i])
                    $('#players').append('<div class="container rounded border border-dark my-2" id="p-' + data['players'][i] + '">' + data['players'][i] + ' </div>');
                    // let player_status = data['players'][i].status;
                }
                if ('player_gameover' in data) {
                    for (let i = 0; i < data['player_gameover'].length; i++) {
                        $('#p-' + data['player_gameover'][i]).addClass('gameover');
                    }
                }
            }
            if (!mp_sync) {
                console.log("Clearing on a non table sync event");
                clear();
            }
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
                                <input type="number" min="1" max="${data['balance']}" class="form-control" name="betamt" id="betamt" required>
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
                        } else {
                            if (primary_signal[i] != "New") {
                                let signal = primary_signal[i];
                                btndiv.append(
                                    `<button class="btn btn-primary btn-round m-2" id="${signal}">${signal}</button>`
                                );
                                $('#' + signal).bind('click', function () {
                                    response['primary']['action'] = signal;
                                    sendresp(response);
                                });
                            }
                        }
                    }
                }
                if ('cards' in data['primary']) {
                    for (let i = 0; i < data['primary']['cards'].length; i++) {
                        $('#playercards').append(
                            '<div class="col-md-2"><img class="mx-auto bg-light m-2 rounded img-fluid" src="' + data['primary']['cards'][i]['url'] + '">'
                        );
                    }
                }
                if ('bet' in data['primary']) {
                    $('#bet_amt').text(data['primary']['bet']);
                }
                if ('end_condition' in data['primary']) {
                    $('#primary_end_condition').text(data['primary']['end_condition']);
                }
            }
            if ('split' in data) {
                if ('signal' in data['split']) {
                    let split_signal = data['split']['signal'];
                    let splitbtndiv = $('#splitbuttondiv');
                    for (let i = 0; i < split_signal.length; i++) {
                        if (split_signal[i] === "Bet") {
                            splitbtndiv.append(
                                `
                                <form id="betform">
                                <input type="number" min="1" max="${data['balance']}" class="form-control" name="betamt" id="betamt" required>
                                <button class="btn btn-primary btn-split btn-round m-2" id="bet">Bet</button>
                                </form>
                                `
                            );
                            $('#betform').submit(function (e) {
                                response['split']['action'] = "bet " + ($('#betamt').val());
                                e.preventDefault();
                                console.log(response);
                                sendresp(response);
                            });
                        } else {
                            let signal = split_signal[i];
                            let btn_id = "split_" + signal;
                            splitbtndiv.append(
                                `<button class="btn btn-primary btn-split btn-round m-2" id="${btn_id}">${signal}</button>`
                            );
                            $('#' + btn_id).bind('click', function () {
                                response['split']['action'] = signal;
                                sendresp(response);
                            });
                        }
                    }
                }
                if ('cards' in data['split']) {
                    for (let i = 0; i < data['split']['cards'].length; i++) {
                        $('#splitcards').append(
                            '<div class="col-md-2"><img class="mx-auto bg-light m-2 rounded img-fluid" src="' + data['split']['cards'][i]['url'] + '">'
                        );
                    }
                }
                if ('bet' in data['split']) {
                    if (data['split']['bet'] != null) {
                        $('#split_bet_amt').text("Split bet: " + data['split']['bet']);
                    } else {
                        $('#split_bet_amt').text("");
                    }
                }
                if ('end_condition' in data['split']) {
                    $('#split_end_condition').text(data['split']['end_condition']);
                }
            }
            if ('dealer_cards' in data) {
                for (let i = 0; i < data['dealer_cards'].length; i++) {
                    $('#dealercards').append(
                        '<div class="col-md-2"><img class="mx-auto bg-light m-2 rounded img-fluid" src="' + data.dealer_cards[i].url + '">'
                    );
                }
            }
            if ('mp_ready_action' in data) {
                mp_sync = true;
                if (data['mp_ready_action'] == "Ready") {
                    $('#mp_buttondiv').append(
                        `<button class="btn btn-primary btn-round m-2" id="mp_ready">${data['mp_ready_action']}</button>`
                    );
                    $('#mp_ready').bind('click', function () {
                        response['ready_action'] = data['mp_ready_action'];
                        sendresp(response);
                        $(this).prop('disabled', true);
                    });
                }
            }
        };
    }
)
;
