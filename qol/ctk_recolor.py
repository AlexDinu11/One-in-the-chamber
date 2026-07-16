import subprocess
import platform

import customtkinter as ctk
from .debug import dprint

INITIAL_FRAME_LAYER = 1

COLOR_OPTIONS = {
    ctk.CTk: {"fg_color": "bg"},

    ctk.CTkLabel: {"fg_color": "transparent",
                   "text_color": "text"},

    ctk.CTkButton: {"fg_color": "btn_normal",
                    "hover_color": "btn_hvr",
                    "text_color": "text",
                    "text_color_disabled": "text_disabled"},

    ctk.CTkFrame: {"fg_color": "bg"},

    ctk.CTkScrollableFrame: [],

    ctk.CTkTabview: {"fg_color": "bg",
                     "segmented_button_fg_color": "bg",
                     "segmented_button_selected_color": "btn_normal",
                     "segmented_button_selected_hover_color": "btn_hvr",
                     "segmented_button_unselected_color": "bg",
                     "text_color": "text",
                     "text_color_disabled": "text_disabled"},

    ctk.CTkSlider: {"fg_color": "#300",
                    "progress_color": "slider_progress",
                    "border_color": "border",
                    "button_color": "btn_normal",
                    "button_hover_color": "btn_hvr"},

    ctk.CTkOptionMenu: {"fg_color": "#300",
                        "button_color": "btn_normal",
                        "button_hover_color": "btn_hvr",
                        "dropdown_fg_color": "#300",
                        "dropdown_hover_color": ""},

}

THEME = {
    "light": {
        "bg1": "#e7e7e7",
        "bg2": "#d7d7d7",
        "bg3": "#c7c7c7",
        "bg4": "#b7b7b7",
        "bg5": "#a7a7a7",

        # Metal
        "border": "#8b9298",

        # Text
        "text": "#1d2023",
        "text_disabled": "#8b9197",

        "segm_btn_fg": "#979da2",

        # Painted steel
        "btn_normal": "#5f7883",
        "btn_hvr": "#708995",
        "btn_disabled": "#a7afb5",

        # Engraved labels
        "label_general": "#585e65",

        # Information plate
        "info": "#182433",

        # Machinery
        "slider_progress": "#6b7178"
    },
    "dark": {
        "bg1": "#1a1a1a",
        "bg2": "#242424",
        "bg3": "#343434",
        "bg4": "#444444",
        "bg5": "#545454",

        "border": "#0f0f0f",

        "text": "#e3dac9",
        "text_disabled": "#555555",

        "segm_btn_fg": "#4a4a4a",

        # Oxidized copper
        "btn_normal": "#2f4f4f",
        "btn_hvr": "#3e5f5f",
        "btn_disabled": "#213737",

        # Brass/aged metal
        "label_general": "#7e8387",

        # Warning plate
        "info": "#1a0f0f",

        "slider_progress": "#9aa0a5"
    }
}

def get_system_theme():
    import winreg

    system = platform.system()

    if system == "Windows":
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value else "dark"

    elif system == "Darwin":
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True
        )

        return "dark" if result.returncode == 0 else "light"

    elif system == "Linux":
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True,
            text=True
        )

        if "dark" in result.stdout.lower():
            return "dark"
        return "light"
    else:
        return "dark"

def recolor(master, settings):

    def recolor_widget(widget, frame_layer):
        widget_location = getattr(widget, "scale_type", "game")
        label_type = getattr(widget, "label_type", None)

        for widget_class in COLOR_OPTIONS:
            if isinstance(widget, widget_class):
                for option in COLOR_OPTIONS[widget_class]:
                    theme_key = COLOR_OPTIONS[widget_class][option]
                    if theme_key == "bg":
                        if option == "segmented_button_unselected_color" or option == "segmented_button_fg_color":
                            theme_key = f"bg{frame_layer+1}"
                        else:
                            theme_key = f"bg{frame_layer}"
                    elif theme_key == "label_general" and label_type == "info":
                        theme_key = "info"
                    if theme_key not in THEME[light_dark] and ("#" in theme_key or theme_key == "transparent"):
                        widget.configure(**{option: theme_key})
                    else:
                        try:
                            widget.configure(**{option: THEME[light_dark][theme_key]})
                        except Exception as e:
                            dprint(e, "error", "red")
                            pass

                    # if widget_class == ctk.CTkLabel:
                    #     if (widget_location == "login" and option == "fg_color") or (label_type == "info" and option == "fg_color"):
                    #         pass
                    # else:


        for child in widget.winfo_children():
            next_layer = frame_layer

            if isinstance(child, (ctk.CTk, ctk.CTkFrame, ctk.CTkScrollableFrame, ctk.CTkTabview)):
                try:
                    # noinspection PyProtectedMember
                    if child in child.master._tab_dict.values():
                        pass
                    else:
                        next_layer += 1
                except:
                    next_layer += 1

            recolor_widget(child, next_layer)

    light_dark = settings["light_dark"].get()

    if light_dark == "system":
        light_dark = get_system_theme()

    recolor_widget(master, INITIAL_FRAME_LAYER)


if __name__ == "__main__":
    root = ctk.CTk()

    frame1 = ctk.CTkFrame(root)
    frame2 = ctk.CTkFrame(frame1)

    ctk.CTkButton(frame1)
    ctk.CTkLabel(frame1)

    ctk.CTkButton(frame2)
    ctk.CTkLabel(frame2)

    ctk.CTkEntry(root)

    recolor(root, {
        "light_dark": "light",
    })

    #it turns out the lbls in the main menu and the ones in the end screen have self.[widget].scale_type = "login" so my theory is that I can use that