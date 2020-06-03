import curses
import string
import argparse
import atexit
import sys
from twist_api import download, stream, get_num_episodes, get_shows

def init_window():
    screen = curses.initscr()
    curses.noecho()
    screen.keypad(True)
    curses.curs_set(0)
    return screen

def exit_window(screen):
    curses.curs_set(1)
    curses.echo()
    screen.keypad(False)
    curses.endwin()

def parse_twist_url(url):
    slug, ep_number = tuple(url[20:].split("/"))
    ep_number = int(ep_number)
    return slug, ep_number

def stream_menu(screen: curses.window, show, slug, num_episodes):
    selected_index = 0
    playing_index = None
    shift = 0
    ymax, xmax = screen.getmaxyx()

    while True:
        screen.clear()
        screen.addstr(0, 0, f"Starting episode? {selected_index + 1 + shift}")
        screen.addstr(1, 0, f"{show}:", curses.A_BOLD)
        max_index = shift + ymax - 1
        num_lines = min(num_episodes, ymax-2)

        for i in range(num_lines):
            try:
                if i == selected_index:
                    screen.addstr(i+2, 0, f"Episode {i + 1 + shift}", curses.A_REVERSE)
                else:
                    screen.addstr(i+2, 0, f"Episode {i + 1 + shift}")
            except:
                raise Exception(f"{i} {shift} {i+2-shift} {num_lines}")
        
        try:
            c = screen.getch()
        except:
            quit()
        
        if c == curses.KEY_UP:
            if selected_index > 0:
                selected_index -= 1
            elif shift > 0:
                shift -= 1 
        elif c == curses.KEY_DOWN:
            if selected_index < ymax - 3:
                selected_index += 1
            elif max_index < num_episodes:
                shift += 1
        elif c in (10, curses.KEY_ENTER):
            start_stream(screen, slug, selected_index + 1 + shift, num_episodes)
        elif chr(c) == "b":
            return False

        screen.refresh()

def start_stream(screen: curses.window, slug, ep_start, num_episodes):
    for i in range(ep_start, num_episodes+1):
        screen.clear()
        screen.addstr(0, 0, f"Playing episode {i}, press Ctrl+C to quit\n")
        screen.refresh()
        if stream(slug, i):
            quit()

def main(screen: curses.window):
    curses.curs_set(0)
    search_term = ""
    selected_index = 0
    shift = 0
    ymax, xmax = screen.getmaxyx()
    shows = get_shows()

    while True:
        screen.clear()
        screen.addstr(0, 0, "Search: "+search_term, curses.A_BOLD)
        max_index = shift+ymax-2
        matches = list(filter(lambda i: search_term.lower() in i.lower(), shows.keys()))
        visible_matches = list(enumerate(matches[shift:max_index+1]))
        max_selection = len(visible_matches) - 1

        if max_selection < ymax-2 and shift > 0:
            shift = 0
            continue

        if selected_index > max_selection:
            selected_index = max_selection

        if selected_index == -1:
            selected_index = 0

        for i, show in visible_matches:
            try:
                if i == selected_index:
                    screen.addstr(i+1, 0, show, curses.A_REVERSE)
                else:
                    screen.addstr(i+1, 0, show)
            except:
                raise Exception(f"{i} {ymax}")

        try:
            c = screen.getch()
        except:
            quit()
        
        if c == curses.KEY_UP:
            if selected_index > 0:
                selected_index -= 1
            elif shift > 0:
                shift -= 1 
        elif c == curses.KEY_DOWN:
            if selected_index < max_selection:
                selected_index += 1
            elif max_index+1 < len(matches):
                shift += 1
        elif c in (10, curses.KEY_ENTER):
            _, show = visible_matches[selected_index]
            slug = shows[show]
            num_episodes = get_num_episodes(slug)
            if stream_menu(screen, show, slug, num_episodes):
                break
        elif c == curses.KEY_BACKSPACE:
            search_term = search_term[:-1]
        elif chr(c) == "\t":
            _, show = visible_matches[selected_index]
            search_term = show
        elif chr(c) in string.printable:
            search_term += chr(c)

        screen.refresh()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download/Stream anime from twist.moe')
    parser.add_argument("--download", "-d", nargs='*', help="Download from twist.moe url. Ex: https://twist.moe/a/hataraku-maou-sama/5")
    parser.add_argument("--stream", "-s", nargs='*', help="Stream from twist.moe url with mplayer")
    parsed = parser.parse_args()
    
    slug_to_show = {j: i for i, j in get_shows().items()}
    
    if parsed.download is None and parsed.stream is None:
        screen = init_window()
        atexit.register(exit_window, screen)
        main(screen)
    else:
        if parsed.download:
            for url in parsed.download:
                slug, ep = parse_twist_url(url)
                show = slug_to_show[slug]
                print(f"Downloading episode {ep} of {show} to {slug}-{ep}.mp4")
                download(slug, ep)
        if parsed.stream:
            for url in parsed.stream:
                slug, ep = parse_twist_url(url)
                show = slug_to_show[slug]
                print(f"Streaming episode {ep} of {show}...")
                stream(slug, ep)