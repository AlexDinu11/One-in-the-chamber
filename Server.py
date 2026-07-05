import socket
import random
import pickle
import struct
from qol.debug import debug

# --- CONFIGURATION ---
PORT = 8723
SERVER_IP = "0.0.0.0"


# --- HELPER FUNCTIONS ---

def send_msg(conn, data):
    """Packages and sends data with a 4-byte length header."""
    serialized = pickle.dumps(data)
    header = struct.pack('>I', len(serialized))
    conn.sendall(header + serialized)
    debug(f"Sent message to all players: {data}", "comm", "yellow")


def recv_msg(conn, raise_on_error=False):
    try:
        header = conn.recv(4)
        if not header: return None
        msg_len = struct.unpack(">I", header)[0]
        data = b''
        while len(data) < msg_len:
            packet = conn.recv(msg_len - len(data))
            if not packet: return None
            data += packet
        return pickle.loads(data)
    except Exception as e:
        if raise_on_error:
            raise
        return None


def generate_magazine(reg):
    """Creates a new mag and returns (list, live_count, blank_count)."""
    mag = [random.randint(0, 1) for _ in range(5)]
    reg += 1
    debug(f"Magazine refilled: {mag}; Magazine regenerations: {reg}", "update") if reg != 1 else debug(f"Magazine refilled: {reg}", "update")
    return mag, mag.count(1), mag.count(0), reg


def generate_items(item_lst, items):
    for p in range(2):
        for _ in range(2):
            i = random.choice(items)
            for q in range(4):
                if item_lst[p][q] == "Empty":
                    item_lst[p][q] = i
                    debug(f"Item added to Player {p}: {i}", "update")
                    break
    debug(f"Items replenished; Player item list: {item_lst}", "update")
    return item_lst


# --- MAIN GAME LOGIC ---

def handle_game():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_IP, PORT))
    server.listen(2)
    debug(f"Listening on {PORT}", "server")

    # 1. Connection Phase
    players = []
    for p in range(2):
        conn, addr = server.accept()
        players.append(conn)
        debug(f"Player {p} at {addr}...", "server")

    for p, conn in enumerate(players):
        send_msg(conn, {"type": "setup", "id": p})

    while True:
        # 2. Initial Game State
        hp = [3, 3]
        dmg = 1
        show_shell = 0
        mk_used = 0
        can = 0
        mag_regens = 0
        last_shell = 2
        items = ["Saw", "Medkit", "Magnifying glass", "Soda Can"]
        all_player_items = [["Empty", "Empty", "Empty", "Empty"], ["Empty", "Empty", "Empty", "Empty"]]

        magazine, live, blank, mag_regens = generate_magazine(mag_regens)
        all_player_items = generate_items(all_player_items, items)
        current_turn = random.randint(0, 1)
        debug(f"State initialized. HP = {hp}, DMG = {dmg}, Items = {all_player_items}", "setup")

        # 3. Game Loop
        while hp[0] != 0 and hp[1] != 0:
            update = {
                "type": "update",
                "turn": current_turn,
                "hp": hp,
                "items": all_player_items,
                "MK": mk_used,
                "dmg": dmg,
                "show_shell": show_shell,
                "can": can,
                "live": live,
                "blank": blank,
                "next_shell": magazine[0],
                "last_shell": last_shell,
                "shells_left": len(magazine),
            }
            for p in players:
                send_msg(p, update)

            active_conn = players[current_turn]
            debug(f"Waiting for Player {current_turn}...", "game")

            data = recv_msg(active_conn)
            if not data:
                debug("PLAYER DISCONNECTED; ENDING SESSION...", "game")
                for p in players:
                    p.close()
                server.close()
                return

            action = data.get("action")
            rtarget = data.get("target")

            if action == "shoot":
                shell = magazine.pop(0)

                if shell == 1:  # LIVE ROUND
                    target = 1 if current_turn == 0 else 0
                    if dmg == 2:
                        if rtarget == "OPPONENT":
                            hp[target] -= 2
                            debug(f"Player {current_turn} shot OPPONENT with LIVE 2x; HP: {hp}", "game")
                        else:
                            hp[current_turn] -= 2
                            debug(f"Player {current_turn} shot SELF with LIVE 2x; HP: {hp}", "game")
                    else:
                        if rtarget == "OPPONENT":
                            hp[target] -= 1
                            debug(f"Player {current_turn} shot OPPONENT with LIVE; HP: {hp}", "game")
                        else:
                            hp[current_turn] -= 1
                            debug(f"Player {current_turn} shot SELF with LIVE; HP: {hp}", "game")
                    current_turn = 1 if current_turn == 0 else 0
                    last_shell = 1
                    debug(f"Turn → Player {current_turn}", "game")
                else:  # BLANK ROUND
                    last_shell = 0
                    if rtarget == "OPPONENT":
                        debug(f"Player {current_turn} shot OPPONENT with BLANK", "game")
                        current_turn = 1 if current_turn == 0 else 0
                        debug(f"Turn → Player {current_turn}", "game")
                    else:
                        debug(f"Player {current_turn} shot SELF with BLANK — keeps turn", "game")

                if not magazine:
                    magazine, live, blank, mag_regens = generate_magazine(mag_regens)

                dmg = 1
                show_shell = 0
                mk_used = 0
                can = 0

            elif action == "item":
                item_used = all_player_items[current_turn][data.get("item_idx")]
                all_player_items[current_turn][data.get("item_idx")] = "Empty"

                if item_used == "Medkit":
                    if current_turn == 0:
                        hp = [min(hp[0] + 1, 3), hp[1]]
                        mk_used = 1
                    else:
                        hp = [hp[0], min(hp[1] + 1, 3)]
                    debug(f"Player {current_turn} used Medkit; HP: {hp[current_turn]}", "game")

                elif item_used == "Saw":
                    dmg = 2
                    debug(f"Player {current_turn} used Saw", "game")

                elif item_used == "Magnifying Glass":
                    show_shell = 1
                    debug(f"Player {current_turn} used Magnifying Glass", "game")

                elif item_used == "Soda Can":
                    can = 1
                    last_shell = magazine.pop(0)
                    debug(f"Player {current_turn} used Soda Can; Shell popped: {last_shell}", "game")

                else:
                    debug(f"Player {current_turn} used invalid item: {item_used}", "error", "red")

        # 4. Send Winner
        loser = next((i for i in range(2) if hp[i] == 0), None)
        if loser is not None:
            winner_msg = {
                "type": "winner",
                "hp": hp,
                "winner": 1 if loser == 0 else 0,
            }
            for p in players:
                send_msg(p, winner_msg)

        # 5. Wait for Rematch
        players_ready = [False, False]
        disconnect = False

        while not all(players_ready):
            for i, p in enumerate(players):
                if not players_ready[i]:
                    p.setblocking(False)
                    try:
                        data = recv_msg(p, raise_on_error=True)
                    except:
                        p.setblocking(True)
                        continue

                    p.setblocking(True)

                    if not data:
                        debug("Player disconnected, closing session", "END", "blue")
                        disconnect = True
                        break

                    if data.get("action") == "rematch":
                        players_ready[i] = True
                        for pp in players:
                            send_msg(pp, {"type": "waiting", "players_ready": players_ready})

                if disconnect:
                    break

            if disconnect:
                break

        if disconnect:
            break

        for p, conn in enumerate(players):
            send_msg(conn, {"type": "setup", "id": p})

    for p in players:
        p.close()
    server.close()


if __name__ == "__main__":
    handle_game()