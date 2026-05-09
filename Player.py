import struct
import customtkinter as ctk
import socket
import threading
import pickle
from qol.debug import debug


# noinspection PyTypeChecker
class MultiplierLabel(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        # Start with no text so it's hidden
        super().__init__(master, text="-------------", font=("Stencil", 32), fg_color="#1A0F0F", corner_radius=2, text_color="#3E1605", **kwargs)

        self.colors = ["#3E1605", "#5E2106", "#822F09", "#A63D0B", "#C94E10", "#ED6814"]
        self.index = 0
        self.direction = -1
        self.active = False
        self.current_msg = ""  # Track what the label says

    def animate(self):
        if self.active:
            self.index += self.direction
            if self.index >= len(self.colors) - 1 or self.index <= 0:
                self.direction *= -1

            self.configure(text=self.current_msg, text_color=self.colors[self.index])
        else:
            self.configure(text="-------------", text_color="#3E1605")

        self.after(80, self.animate)

    def toggle(self, state: bool, message: str = "", duration: int = None):
        """Call with (True, 'MY TEXT', duration) to show or (False) to hide."""

        while len(message) < 13:
            message = "-" + message + "-"

        self.active = state
        self.current_msg = message
        if state:
            self.index = len(self.colors) - 1  # Reset to the brightest colorx
            self.direction = -1
            self.animate()

            if duration:
                self.after(duration, lambda: self.toggle(False))

            debug(f"Blinking activated: text={self.current_msg}, duration={duration}\n", "blinking", "yellow")
        else:
            pass


# noinspection PyAttributeOutsideInit
class BuckshotClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        # --- WINDOW SETUP ---
        self.title("Buckshot Player")
        self.after(0, lambda: self.state('zoomed'))
        self.socket = None
        self.resize_timer = None
        self.last_size = (0, 0)
        self.bind('<Configure>', self.on_resize)

        # Resize Constants
        self.font_add_constant1 = 0
        self.font_add_constant2 = 0
        self.font_add_constant3 = 0
        self.font_div_constant = 48
        self.font_size1 = 0
        self.font_size2 = 0
        self.font_size3 = 0

        self.label_add_constant1 = 0
        self.label_add_constant2 = 0
        self.label_add_constant3 = 0
        self.label_div_constant = 15
        self.label_size1_x = 0
        self.label_size1_y = 0
        self.label_size2_x = 0
        self.label_size2_y = 0
        self.label_size3_x = 0
        self.label_size3_y = 0

        # --- INITIALIZE UI ---
        self.initial_resize()

    def setup_login_ui(self):
        """Initial screen to enter IP and Port."""
        self.title_lbl = ctk.CTkLabel(self, text="Buckshot Roulette", font=("Stencil", self.font_size1), width=self.label_size1_x, height=self.label_size1_y)
        self.title_lbl.pack(pady=10, padx=100)
        self.title_lbl.font_scale_type = "huge"
        self.title_lbl.scale_type = "login"

        self.status_lbl = ctk.CTkLabel(self, text="Connect to server", font=("Stencil", 30))
        self.status_lbl.pack(pady=(10, 100), padx=100)
        self.status_lbl.font_scale_type = "med"
        self.status_lbl.scale_type = "login"

        self.ip_ent = ctk.CTkEntry(self, placeholder_text="IP", width=150, justify="center")
        self.ip_ent.pack(pady=5)
        self.ip_ent.font_scale_type = "small"
        self.ip_ent.scale_type = "login"

        self.port_ent = ctk.CTkEntry(self, placeholder_text="PORT", width=150, justify="center")
        self.port_ent.pack(pady=5)
        self.port_ent.insert(0, "8723")
        self.port_ent.font_scale_type = "small"
        self.port_ent.scale_type = "login"

        self.conn_btn = ctk.CTkButton(self, text="Connect", command=self.connect_to_server)
        self.conn_btn.pack(pady=20)
        self.conn_btn.font_scale_type = "small"
        self.conn_btn.scale_type = "login"

    def on_resize(self, event):
        # ONLY trigger if the event is for the Window itself (not a button/frame)
        if event.widget != self:
            return

        # ONLY trigger if the dimensions are actually different from the last run
        current_size = (event.width, event.height)
        if current_size == self.last_size:
            return

        if self.resize_timer:
            self.after_cancel(self.resize_timer)

        self.resize_timer = self.after(1000, self.handle_resize)

    def initial_resize(self):
        if debug_active:
            debug("initial_resize", "debug")
        self.update()
        self.l = ctk.CTkLabel(self, text="")
        self.l.pack()
        self.handle_resize()
        self.after(150, self.setup_login_ui)

    # noinspection PyUnresolvedReferences
    def handle_resize(self):

        # 2. Recursive function to find ALL widgets in ALL frames
        def resize_all(parent):
            self.update_idletasks()
            self.scale = min(self.winfo_width() / 1920, self.winfo_height() / 1080)

                # --- FONT SCALING ---
            font_size_huge = int(85 * self.scale) + 12
            font_size_med = int(40 * self.scale) + 10
            font_size_sma = int(30 * self.scale) + 8

            # --- WIDGET DIMENSIONS ---
            box_width_huge = int(350 * self.scale) + 75
            box_height_huge = int(80 * self.scale) + 15

            box_width_med = int(250 * self.scale) + 50
            box_height_med = int(50 * self.scale) + 10

            box_width_sma = int(200 * self.scale) + 30
            box_height_sma = int(40 * self.scale) + 6

            for widget in parent.winfo_children():
                # If this is a container, look inside it too
                if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
                    resize_all(widget)

                # Get the scale type you assigned in build_game_interface
                # Default to "med" if you forgot to set one
                w_scale = getattr(widget, "font_scale_type", "med")
                scale_type = getattr(widget, "scale_type", "game")
                lbl_type = getattr(widget, "lbl_type", 0)

                # Determine values based on w_scale and scale_type
                if scale_type == "login":
                    if w_scale == "huge":
                        w, h, f = box_width_huge, box_height_huge, font_size_huge
                    elif w_scale == "small":
                        w, h, f = box_width_sma, box_height_sma, font_size_sma
                    else:
                        w, h, f = box_width_med, box_height_med, font_size_med
                else:
                    if w_scale == "huge":
                        w, h, f, = box_width_huge/1.5, box_height_huge/1.5, font_size_huge/1.5
                    elif w_scale == "small":
                        w, h, f = box_width_sma/1.5, box_height_sma/1.5, font_size_sma/1.5
                    else:
                        w, h, f = box_width_med/1.5, box_height_med/1.5, font_size_med/1.5

                # 3. Apply changes (Safety check for specific widget types)
                try:
                    if isinstance(widget, (ctk.CTkButton, ctk.CTkEntry)):
                        widget.configure(font=("Stencil", f), width=w, height=h)
                    elif isinstance(widget, ctk.CTkLabel) and lbl_type == 1:  # if is multiplier label, it's smaller than game state labels
                        widget.configure(font=("Stencil", f), width=w*1.3, height=h)
                    elif isinstance(widget, ctk.CTkLabel) and lbl_type == 0:
                        widget.configure(font=("Stencil", f), width=w, height=h)
                    elif isinstance(widget, ctk.CTkProgressBar):
                        widget.configure(height=h) # Progress bars don't take fonts
                except Exception:
                    pass
                if debug_active:
                    debug(f"w = {w}, h = {h}, f = {f}")

        # Start the recursion from the main window
        resize_all(self)
        debug(f"UI Scaled to: {self.scale:.2f}", "settings", "green")


    # --- 3. NETWORKING ---

    def connect_to_server(self):
        host = self.ip_ent.get()
        try:
            port = int(self.port_ent.get())
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            self.socket = sock  # only assign AFTER successful connect
            self.conn_btn.configure(state="disabled")
            self.status_lbl.configure(text="Awaiting second player...")
            threading.Thread(target=self.receive_loop, daemon=True).start()
        except Exception as e:
            self.status_lbl.configure(text="Server Offline!")
            debug(f"{e}", "error", "red")

    def receive_loop(self):
        """Listens for data and routes it to the correct UI function."""
        while True:
            try:
                header = self.recv_exactly(4)
                if not header: break
                msg_len = struct.unpack(">I", header)[0]
                data = pickle.loads(self.recv_exactly(msg_len))

                # Use .after to ensure UI updates happen on the main thread
                self.after(0, self.handle_message, data)
            except:
                break

    def recv_exactly(self, n):
        data = b''
        while len(data) < n:
            packet = self.socket.recv(n - len(data))
            if not packet: return None
            data += packet
        return data

    def request_rematch(self):
        self.play_again.configure(state="disabled", text="WAITING")
        self.send_action("rematch")

    def send_action(self, action, target = None, item_idx = None):
        """Sends player move to the server."""
        payload = {"action": action, "target": target, "item_idx": item_idx}
        debug(f"Sending payload: {payload}", "comm", "yellow")
        data = pickle.dumps(payload)
        header = struct.pack(">I", len(data))
        self.socket.sendall(header + data)

    def handle_message(self, data):
        if data["type"] == "setup":
            self.my_id = data["id"]
            self.opp_id = 1 if self.my_id == 0 else 0
            self.build_game_interface()
            self.p0_title.configure(text=f"PLAYER {self.my_id} (YOU)")
            debug(f"Received setup: My ID = {self.my_id}", "comm", "yellow")

        elif data["type"] == "update":
            debug(f"Received update: {data}", "comm", "yellow")
            self.refresh_game_state(data)

        elif data["type"] == "winner":
            debug(f"Match ended! End confirmation: {data}", "comm", "yellow")
            self.build_end_screen(data)

    # --- 4. GAME UI CONSTRUCTION (Run Once) ---

    def build_game_interface(self):
        """Destroys login UI and builds the persistent game frames."""
        def delete_all(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
                    delete_all(widget)
                widget.destroy()

        delete_all(self)

        # --- TITLE ---
        self.w_title = ctk.CTkLabel(self, text="Buckshot roulette", font=("Stencil", 20))
        self.w_title.pack(anchor="w", padx=5)
        self.w_title.font_scale_type = "small"

        # --- LEFT PANEL (YOU) ---
        self.p0_frame = ctk.CTkFrame(self, fg_color="#1B1B1B", border_color="#0F0F0F")
        self.p0_frame.place(relx=0, rely=0, relwidth=0.6, relheight=1.0)

        self.p0_title = ctk.CTkLabel(self.p0_frame, text="YOU", font=("Stencil", 30))
        self.p0_title.pack(pady=10)
        self.p0_title.font_scale_type = "med"

        self.p0_hp = ctk.CTkProgressBar(self.p0_frame, height=30, fg_color="#1A0F0F", border_color="#3E2731", border_width=3, corner_radius=10, progress_color="#630D0D")
        self.p0_hp.pack(pady=5, padx=20, fill="x")
        self.p0_hp.set(1.0)
        self.p0_hp.font_scale_type = "med"

        # Round labels

        self.rnd_coll = ctk.CTkFrame(self.p0_frame, fg_color="#1B1B1B")
        self.rnd_coll.pack(pady=10, fill="x")

        self.rnd_lbl = ctk.CTkFrame(self.rnd_coll, fg_color="#1B1B1B")
        self.rnd_lbl.pack(pady=20)

        self.last_shell_lbl = MultiplierLabel(self.rnd_lbl)
        self.last_shell_lbl.pack(pady=(10, 0), side="left")
        self.last_shell_lbl.font_scale_type = "med"
        self.last_shell_lbl.lbl_type = 1

        self.t_live_lbl = ctk.CTkLabel(self.rnd_lbl, text_color="#3E1605", font=("Stencil", 32), fg_color="#1A0F0F", corner_radius=2, text="-------------")
        self.t_live_lbl.pack(pady=(10,0), side="left")
        self.t_live_lbl.font_scale_type = "med"
        self.t_live_lbl.lbl_type = 1

        self.t_blank_lbl = ctk.CTkLabel(self.rnd_lbl, text_color="#3E1605", font=("Stencil", 32), fg_color="#1A0F0F", corner_radius=2, text="-------------")
        self.t_blank_lbl.pack(pady=(10,0), side="left")
        self.t_blank_lbl.font_scale_type = "med"
        self.t_blank_lbl.lbl_type = 1

        self.sh_shell = MultiplierLabel(self.rnd_lbl)
        self.sh_shell.pack(pady=(10, 0), side="left")
        self.sh_shell.font_scale_type = "med"
        self.sh_shell.lbl_type = 1

        # Multipliers
        self.multipliers = ctk.CTkFrame(self.p0_frame, fg_color="#1B1B1B", border_color="#0F0F0F")
        self.multipliers.pack(pady=1, padx=20, expand=True)

        self.ddmg = MultiplierLabel(self.multipliers)
        self.ddmg.pack(pady=(10, 0), side="left")
        self.ddmg.font_scale_type = "med"

        self.mk_lbl = MultiplierLabel(self.multipliers)
        self.mk_lbl.pack(pady=(10, 0), side="left")
        self.mk_lbl.font_scale_type = "med"

        self.magnifying_lbl = MultiplierLabel(self.multipliers)
        self.magnifying_lbl.pack(pady=(10, 0), side="left")
        self.magnifying_lbl.font_scale_type = "med"

        self.skip_rnd = MultiplierLabel(self.multipliers)
        self.skip_rnd.pack(pady=(10, 0), side="left")
        self.skip_rnd.font_scale_type = "med"

        # Action Buttons (Shoot)
        self.p0_shoot_row = ctk.CTkFrame(self.p0_frame, fg_color="#1F1F1F", border_color="#0F0F0F", height=80)
        self.p0_shoot_row.pack(pady=1, fill="x", expand=True)

        self.btn_opp = ctk.CTkButton(self.p0_shoot_row, text="Shoot Opponent", height=75, fg_color="#2F4F4F", hover_color="#3E5F5F", border_color="#1A2421", border_width=3, corner_radius=2, text_color="#E3DAC9",
                                     command=lambda: self.send_action("shoot", "OPPONENT", None))
        self.btn_opp.pack(side="left", padx=10, expand=True)
        self.btn_opp.font_scale_type = "med"

        self.btn_self = ctk.CTkButton(self.p0_shoot_row, text="Shoot Self", height=75, fg_color="#2F4F4F", hover_color="#3E5F5F", border_color="#1A2421", border_width=3, corner_radius=2, text_color="#E3DAC9",
                                      command=lambda: self.send_action("shoot", "SELF", None))
        self.btn_self.pack(side="left", padx=10, expand=True)
        self.btn_self.font_scale_type = "med"

        # Item Buttons Row
        self.p0_item_row = ctk.CTkFrame(self.p0_frame, fg_color="#1F1F1F", border_color="#0F0F0F")
        self.p0_item_row.pack(pady=10, fill="x", padx=10, expand=True)

        self.item_btns = []
        for i in range(4):
            btn = ctk.CTkButton(self.p0_item_row, text=f"Empty", width=150, height=100, fg_color="#2F4F4F", hover_color="#3E5F5F", border_color="#1A2421", border_width=3, corner_radius=2, text_color="#E3DAC9",
                                command= lambda idx=i: self.send_action("item", None, idx))
            btn.pack(side="left", padx=5, pady=5, expand=True)
            btn.font_scale_type = "small"
            self.item_btns.append(btn)

        # --- RIGHT PANEL (OPPONENT) ---
        self.p1_frame = ctk.CTkFrame(self, fg_color="gray15")
        self.p1_frame.place(relx=0.6, rely=0, relwidth=0.4, relheight=1.0)

        self.p1_title = ctk.CTkLabel(self.p1_frame, text="OPPONENT", font=("Stencil", 30))
        self.p1_title.pack(pady=10)
        self.p1_title.font_scale_type = "med"

        self.p1_hp = ctk.CTkProgressBar(self.p1_frame, height=30, fg_color="#1A0F0F", border_color="#3E2731", border_width=3, corner_radius=10, progress_color="#630D0D")
        self.p1_hp.pack(pady=(5, 175), padx=20, fill="x")
        self.p1_hp.set(1.0)
        self.p1_hp.font_scale_type = "med"


        # Item Buttons Row
        self.p1_items_frame = ctk.CTkFrame(self.p1_frame, fg_color="#1F1F1F")
        self.p1_items_frame.pack(pady=20, fill="x", padx=10)
        self.p1_item_row1 = ctk.CTkFrame(self.p1_items_frame, fg_color="transparent")
        self.p1_item_row1.pack(pady=20, fill="x", padx=10)
        self.p1_item_row2 = ctk.CTkFrame(self.p1_items_frame, fg_color="transparent")
        self.p1_item_row2.pack(pady=20, fill="x", padx=10)

        self.opp_item_btns = []
        for i in range(4):
            if i in (0, 1):
                btn = ctk.CTkButton(self.p1_item_row1, text=f"Empty", width=150, height=100, state="disabled", fg_color="#2F4F4F", hover_color="#3E5F5F", border_color="#1A2421", border_width=3, corner_radius=2, text_color="#E3DAC9")
                btn.pack(side="left", padx=5, pady=5, expand=True)
                btn.font_scale_type = "med"
                self.opp_item_btns.append(btn)
            if i in (2, 3):
                btn = ctk.CTkButton(self.p1_item_row2, text=f"Empty", width=150, height=100, state="disabled", fg_color="#2F4F4F", hover_color="#3E5F5F", border_color="#1A2421", border_width=3, corner_radius=2, text_color="#E3DAC9")
                btn.pack(side="left", padx=5, pady=5, expand=True)
                btn.font_scale_type = "med"
                self.opp_item_btns.append(btn)

        self.after(0, lambda:self.handle_resize())

    # --- 5. LOGIC & UPDATES (Run repeatedly) ---

    def refresh_game_state(self, data):
        """Updates values without rebuilding widgets."""
        # 1. Update HP (Assuming 3 is max)
        self.p0_hp.set(data["hp"][self.my_id] / 3)
        self.p1_hp.set(data["hp"][self.opp_id] / 3)

        # 2. Update Turn State (Enable/Disable Buttons)
        is_my_turn = (data["turn"] == self.my_id)
        btn_state = "normal" if is_my_turn else "disabled"

        self.btn_opp.configure(state=btn_state)
        self.btn_self.configure(state=btn_state)

        self.t_live_lbl.configure(text=f"Live: {data['live']}", text_color="#ED6814")
        self.t_blank_lbl.configure(text=f"Blank: {data['blank']}", text_color="#ED6814")

        # Update Blinkers
        if data["dmg"] == 2:
            self.ddmg.toggle(True, "2X DMG")
        elif data["dmg"] == 1:
            self.ddmg.toggle(False)

        if data["show_shell"] == 1:
            if data["next_shell"] == 1:
                self.sh_shell.toggle(True, "NEXT: LIVE", 3000)
            else:
                self.sh_shell.toggle(True, "NEXT: BLANK", 3000)
            self.magnifying_lbl.toggle(True, "SHELL PEEK", 3000)

        if data["can"] == 1:
            self.skip_rnd.toggle(True, "EMPTIED", 3000)

        if data["last_shell"] == 1:
            self.last_shell_lbl.toggle(True, "BANG", 3000)
        elif data["last_shell"] == 0:
            self.last_shell_lbl.toggle(True, "CLICK", 3000)

        if data["MK"] == 1:
            self.mk_lbl.toggle(True, "HP+1", 3000)

        # 3. Update Item Buttons text (if server sends an 'items' list)
        if "items" in data:
            my_items = data["items"][self.my_id]
            for i in range(4):
                if i < len(my_items):
                    self.item_btns[i].configure(text=my_items[i], state=btn_state)
                else:
                    self.item_btns[i].configure(text="Empty", state="disabled")
            opp_items = data["items"][self.opp_id]
            for i in range(4):
                if i < len(opp_items):
                    self.opp_item_btns[i].configure(text=opp_items[i])
                else:
                    self.opp_item_btns[i].configure(text="Empty")

    def build_end_screen(self, data):
        def delete_all(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
                    delete_all(widget)
                widget.destroy()

        delete_all(self)

        hp_self = data["hp"][self.my_id]
        hp_opp = data["hp"][self.opp_id]
        won = hp_self != 0

        # --- CENTERED CONTAINER ---
        self.end_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.end_frame.place(relx=0.5, rely=0.5, anchor="center")  # perfectly centered

        # --- WIN/LOSE TITLE ---
        self.winner_lbl = ctk.CTkLabel(
            self.end_frame,
            text="YOU WON" if won else "YOU DIED",
            font=("Stencil", 72),
            text_color="#ED6814" if won else "#630D0D",
        )
        self.winner_lbl.pack(pady=(0, 40))
        self.winner_lbl.font_scale_type = "huge"
        self.winner_lbl.scale_type = "login"

        # --- SEPARATOR ---
        ctk.CTkFrame(self.end_frame, height=2, fg_color="#3E1605", width=400).pack(pady=(0, 40))

        # --- HP DISPLAY (side by side) ---
        self.hp_frame = ctk.CTkFrame(self.end_frame, fg_color="transparent")
        self.hp_frame.pack(pady=(0, 40))

        self.hp_self_lbl = ctk.CTkLabel(
            self.hp_frame,
            text=f"YOUR HP\n{hp_self}",
            font=("Stencil", 36),
            fg_color="#1A0F0F",
            corner_radius=8,
            width=150,
            height=100,
            text_color="#ED6814" if won else "#630D0D",
        )
        self.hp_self_lbl.pack(side="left", padx=20)
        self.hp_self_lbl.font_scale_type = "med"
        self.hp_self_lbl.scale_type = "login"

        self.hp_opp_lbl = ctk.CTkLabel(
            self.hp_frame,
            text=f"OPP HP\n{hp_opp}",
            font=("Stencil", 36),
            fg_color="#1A0F0F",
            corner_radius=8,
            width=150,
            height=100,
            text_color="#630D0D" if won else "#ED6814",
        )
        self.hp_opp_lbl.pack(side="left", padx=20)
        self.hp_opp_lbl.font_scale_type = "med"
        self.hp_opp_lbl.scale_type = "login"

        # --- PLAY AGAIN BUTTON ---
        self.play_again = ctk.CTkButton(
            self.end_frame,
            text="PLAY AGAIN",
            height=75,
            fg_color="#2F4F4F",
            hover_color="#3E5F5F",
            border_color="#1A2421",
            border_width=3,
            corner_radius=2,
            text_color="#E3DAC9",
            command=self.request_rematch
        )
        self.play_again.pack(pady=(0, 20))
        self.play_again.font_scale_type = "med"
        self.play_again.scale_type = "login"

        self.after(0, lambda: self.handle_resize())


if __name__ == "__main__":

    check = input()
    if check=="567812":
        _debug_ = input()
        ff = input()
        if ff=="549832":
            debug("Family friendly end turned off", "warning", "red")
            family_friendly = True
        else:
            family_friendly = False
    else:
        family_friendly = False
    try:
        if _debug_=="529674":
            debug_active = True
        else:
            debug_active = False
    except:
        debug_active = False
        pass

    app = BuckshotClient()
    app.mainloop()
