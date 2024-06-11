$(document).ready(function() {

    $("#comboBox1").val("");
    updateComboBox(1, '#comboBox1', ['#comboBox2', '#comboBox3', '#comboBox4', '#comboBox5']);
    $("#comboBox7").val("");
    $('#search-input').val("");


    $('#comboBox1').change(function() {
        updateComboBox(1, '#comboBox1', ['#comboBox2', '#comboBox3', '#comboBox4', '#comboBox5']);
    });

    $('#comboBox2').change(function() {
        updateComboBox(2, '#comboBox2', ['#comboBox3', '#comboBox4', '#comboBox5']);
    });

    $('#comboBox3').change(function() {
        updateComboBox(3, '#comboBox3', ['#comboBox4', '#comboBox5']);
    });

    $('#comboBox4').change(function() {
        updateComboBox(4, '#comboBox4', ['#comboBox5']);
    });

    $('#comboBox5').change(function() {
        var selectedValue = $(this).val();
        var targetId = '#students-schedule';
        if (selectedValue) {
            // Формирование ajax-запроса, создание таблички и ее отображение
            $.ajax({
                url: get_options_url,
                type: "GET",
                data: { level: 5, uni_name: $('#comboBox1').val(), fac_name: $('#comboBox2').val(), education_type: $('#comboBox3').val(), course: $('#comboBox4').val(), group_name: $('#comboBox5').val()},
                success: function(data) {
                    var rows = data.options;
                    $(targetId).empty();
                    if (rows.length) {
                        $('#infoText').removeClass('show');
                        var header = '<thead class="align-items-center">\n<tr>\n';
                        rows.shift().forEach(function(column_name) {
                            header += `<th class='text-center'>${column_name}</th>\n`;
                        });
                        $(targetId).append(header + '</tr>\n</thead>\n<tbody>\n');
                        header = null;
                        var row;
                        rows.forEach(function(buffer) {
                            if (typeof buffer === 'string') {
                                $(targetId).append(`<tr>\n<td colspan="9" class="text-center text-xl">${buffer}</td>\n</tr>\n`);
                            } else {
                                row = '<tr>\n';
                                buffer.forEach(function(field) {
                                    row += `<td>${field === null ? "" : field}</td>\n`
                                });
                                $(targetId).append(row + '</tr>\n');
                            } 
                        });
                        row = null;
                    } else {
                        $(targetId).append('<h2 class="text-center">Расписание не найдено</h2>');
                        $('#infoText').addClass('show');
                    }
                }
            });
            $(targetId).addClass('show');
        } else {
            // Если табличка была отображена, то убираем ее
            if (!$(targetId).prop('disabled')) {
                $(targetId).empty();
                $(targetId).removeClass('show');
                $('#infoText').addClass('show');
            }
        };
    });

    function updateComboBox(level, sourceId, targetIds) {
        $('#students-schedule').empty();
        $('#students-schedule').removeClass('show');
        $('#infoText').addClass('show');
        targetIds.forEach(function(targetId) {
            $(targetId).empty();
            $(targetId).append('<option value="" class="text-grey">Выберите</option>');
            $(targetId).prop('disabled', true);
        });
        var selectedValue = $(sourceId).val();
        var targetId = targetIds.shift();
        if (selectedValue) {
            targetIds.forEach(function(targetId) {
                if (!$(targetId).prop('disabled')){
                    $(targetId).empty();
                    $(targetId).append('<option value="" class="text-grey">Выберите</option>');
                    $(targetId).prop('disabled', true);
                }
            });
            $.ajax({
                url: get_options_url,
                type: "GET",
                data: { level: level, uni_name: $('#comboBox1').val(), fac_name: $('#comboBox2').val(), education_type: $('#comboBox3').val(), course: $('#comboBox4').val()},
                success: function(data) {
                    var options = data.options;
                    $(targetId).empty();
                    $(targetId).append('<option value="" class="text-grey">Выберите</option>');
                    options.forEach(function(option) {
                        $(targetId).append('<option value="' + option + '">' + option + '</option>');
                    });
                    $(targetId).prop('disabled', false);
                }
            });
        } else {
            targetIds.forEach(function(targetId) {
                if (!$(targetId).prop('disabled')){
                    $(targetId).empty();
                    $(targetId).append('<option value="" class="text-grey">Выберите</option>');
                    $(targetId).prop('disabled', true);
                }
            })
        }
    };
    $("#btn1").click(function() {
        $("#comboBox7").val("");
        $('#search-input').val("");
        $("#content1").show();
        $("#content2").hide();
        $("#btn1").addClass("active");
        $("#btn2").removeClass("active");
      });

    $("#btn2").click(function() {
        $("#comboBox1").val("");
        updateComboBox(1, '#comboBox1', ['#comboBox2', '#comboBox3', '#comboBox4', '#comboBox5']);
        $("#content1").hide();
        $('#search-input').prop('disabled', true)
        $("#content2").show();
        $("#btn1").removeClass("active");
        $("#btn2").addClass("active");
      });

    $('#comboBox7').change(function() {
        $('#teacher-schedule').empty();
        $('#teacher-schedule').removeClass('show');
        $('#teacher-link').empty();
        $('#search-input').val("");
        if ($(this).val()) {
            $('#search-input').prop('disabled', false);
        } else {
            $('#search-input').prop('disabled', true);
            $('#infoText').addClass('show');
        }
    });

    $('#search-input').on('click input', function() {
        var query = $(this).val();
        if (query.length >= 2) {
            $.ajax({
                url: search_url,
                type: "GET",
                data: { query: query, uni_name: $('#comboBox7').val() },
                success: function(data) {
                    $('#suggestions').empty();
                    if (data.length) {
                        data.forEach(function(item) {
                            $('#suggestions').append('<a href="#" class="list-group-item list-group-item-action">' + item + '</a>');
                        });
                        $('#suggestions').addClass('show');
                    } else {
                        $('#suggestions').removeClass('show');
                    }
                }
            });
        } else {
            $('#suggestions').empty().removeClass('show');
        }
    });

    function emptyModal() {
        $('#photoModalLabel').empty();
        $('#information').empty();
    }

    function createModal(tag, targetId = null) {
        if (targetId) {
            $(targetId).empty();
            $(targetId).append(tag);
        }
        emptyModal();
        $('#photoModalLabel').append('<b>Информационное окно</b>');
        if (typeof tag === 'string') {
            var bufferDiv = document.createElement('div');
            bufferDiv.innerHTML = tag;
            tag = bufferDiv.firstChild;
            bufferDiv = null;
            $('#information').append(tag.getAttribute('data-information'));
        }
        else {
            $('#information').append(tag.data('information'));
        }
    }

    // Handle suggestion click
    $('#suggestions').on('click', '.list-group-item', function(e) {
        e.preventDefault();
        $('#search-input').val($(this).text());
        $('#suggestions').removeClass('show');
        var targetId = '#teacher-schedule';
        $.ajax({
            url: get_options_url,
            type: "GET",
            data: { level: 0, teacher_name: $('#search-input').val(), uni_name: $('#comboBox7').val() },
            success: function(data) {
                var rows = data.options;
                createModal(data.tag, '#teacher-link');
                $(targetId).empty();
                if (rows.length) {
                    var header = '<thead class="align-items-center">\n<tr>\n';
                    rows.shift().forEach(function(column_name) {
                        header += `<th class='text-center'>${column_name}</th>\n`;
                    });
                    $(targetId).append(header + '</tr>\n</thead>\n<tbody>\n');
                    header = null;
                    var row;
                    rows.forEach(function(buffer) {
                        if (typeof buffer === 'string') {
                            $(targetId).append(`<tr>\n<td colspan="8" class="text-center text-xl">${buffer}</td>\n</tr>\n`);
                        } else {
                            row = '<tr>\n';
                            buffer.forEach(function(field) {
                                row += `<td>${field === null ? "" : field}</td>\n`
                            });
                            $(targetId).append(row + '</tr>\n');
                        } 
                    });
                    row = null;
                } else {
                    $(targetId).append('<h2 class="text-center">Расписание не найдено</h2>');
                    $('#infoText').addClass('show');
                }
                $('#infoText').removeClass('show');
                $(targetId).addClass('show');
            }
        });
    });

    // Hide dropdown when clicking outside
    $(document).click(function(event) {
        if (!$(event.target).closest('.form-group').length) {
            $('#suggestions').removeClass('show');
        }
    });

    // $('#openModalLink').on('click', function(event) {
    //     event.preventDefault();
    //     $('#myModal').modal('show');
    // });

    $('#teacher-link').on('click', '.openModalButton', function() {
        // var photoFilepath= $(this).data('photo');
        var photoUrl = '/get_photo/' + $(this).data('photo');
        $('#modalImage').attr('src', photoUrl);
        $('#photoModal').modal('show');
    });

    $('.table').on('click', '.teacher-click.openModalButton', function() {
        emptyModal();
        createModal($(this));
        var photoUrl = '/get_photo/' + $(this).data('photo');
        $('#modalImage').attr('src', photoUrl);
        $('#photoModal').modal('show');
    });

    $('.table').on('click', '.enclosure-click.openModalButton', function() {
        emptyModal();
        createModal($(this));
        var photoUrl = '/get_photo/' + $(this).data('photo');
        $('#modalImage').attr('src', photoUrl);
        $('#photoModal').modal('show');
    });
});