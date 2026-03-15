def get_servers(movie):

    search = movie.replace(" ","+")

    return [
        f"https://new4.hdhub4u.fo/?s={search}",
        f"https://123mkv.bar/?s={search}",
        f"https://mkvcinemas.sb/?s={search}",
        f"https://worldfree4u.ist/?s={search}",
        f"https://bolly4u.gifts/?s={search}",
        f"https://1filmyfly.org/?s={search}"
    ]
