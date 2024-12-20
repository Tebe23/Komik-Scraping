$(document).ready(function () {
    // Handle "Load More Popular"
    $('#popular-next').on('click', function () {
        const button = $(this);
        const nextUrl = button.data('next');

        $.ajax({
            url: '/load_more',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ url: nextUrl }),
            success: function (response) {
                const komikData = response.komik_data;
                const nextPage = response.next_page;

                komikData.forEach(komik => {
                    $('#popular-list').append(`
                        <div class="komik-item">
                            <img src="${komik.image}" alt="${komik.title}">
                            <div class="komik-details">
                                <h3><a href="${komik.link}" target="_blank">${komik.title}</a></h3>
                                <p>Chapter: ${komik.chapter}</p>
                                <p>Rating: ${komik.score}</p>
                            </div>
                        </div>
                    `);
                });

                if (nextPage) {
                    button.data('next', nextPage);
                } else {
                    button.hide();
                }
            },
            error: function (xhr, status, error) {
                console.error('AJAX Error:', status, error);
            }
        });
    });

    // Handle "Load More Latest"
    $('#latest-next').on('click', function () {
        const button = $(this);
        const nextUrl = button.data('next');

        $.ajax({
            url: '/load_more',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ url: nextUrl }),
            success: function (response) {
                const komikData = response.komik_data;
                const nextPage = response.next_page;

                komikData.forEach(komik => {
                    $('#latest-list').append(`
                        <div class="komik-item">
                            <img src="${komik.image}" alt="${komik.title}">
                            <div class="komik-details">
                                <h3><a href="${komik.link}" target="_blank">${komik.title}</a></h3>
                                <p>Chapter: ${komik.chapter}</p>
                                <p>Rating: ${komik.score}</p>
                            </div>
                        </div>
                    `);
                });

                if (nextPage) {
                    button.data('next', nextPage);
                } else {
                    button.hide();
                }
            },
            error: function (xhr, status, error) {
                console.error('AJAX Error:', status, error);
            }
        });
    });
});
