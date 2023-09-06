import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import compiler


class GUI:

    def __init__(self):
        super().__init__()
        self.selected_input = False
        self.selected_output = False
        self.input_type = None
        self.input_files = []
        self.input_name = None
        self.input_path = None
        self.output_folder_path = None
        self.root = tk.Tk()
        self.root.geometry("600x300")
        self.root.resizable(False, False)
        self.root.title("Odour Signal Compiler")

        # code for generate button

        self.gen_button_frame = tk.Frame(self.root, width=50, height=50)
        self.gen_button_frame.pack(side="bottom", anchor="s", padx=5, pady=(0, 30))
        self.generate_button = tk.Button(self.gen_button_frame, width=10, height=3, text="Generate",
                                         command=self.generate)
        self.generate_button.pack()

        # progress bars
        self.progress_frame = tk.Frame(self.root)
        self.progress_frame.pack(side="bottom", anchor="center", pady=(0, 20))
        self.progress_frame_label = tk.Label(self.progress_frame, text="Progress", font=("Arial", 10))
        self.progress_frame_label.pack(side="top")
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.pack()
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 100

        # code for input frame

        self.input_frame = tk.Frame(self.root, width=285, height=100, relief="sunken", borderwidth=1)
        self.input_frame.pack_propagate(0)
        self.input_frame.pack(side="left", anchor="nw", padx=10, pady=10)
        self.input_frame_title = tk.Label(self.input_frame, text="Input", font=("Arial", 10))
        self.input_frame_title.pack(side="top", padx=0, pady=0)
        self.input_file_name = tk.Label(self.input_frame, text="Select a file/folder", font=("Arial", 8), background=
                                        "white", height=2, width=30)
        self.input_file_name.pack(side="left", padx=5, pady=5)
        self.select_file = tk.Button(self.input_frame, width=10, height=1, text="Load", command=self.select_file)
        self.select_file.pack(side="top", anchor="ne", padx=5, pady=(7, 2))
        self.select_folder = tk.Button(self.input_frame, width=10, height=1, text="Load Folder",
                                       command=self.select_folder)
        self.select_folder.pack(side="right", anchor="se", padx=5, pady=(2, 7))

        # code for output frame

        self.output_frame = tk.Frame(self.root, width=285, height=100, relief="sunken", borderwidth=1)
        self.output_frame.pack_propagate(0)
        self.output_frame.pack(side="right", anchor="ne", padx=10, pady=10)
        self.output_frame_title = tk.Label(self.output_frame, text="Destination", font=("Arial", 10))
        self.output_frame_title.pack(side="top", padx=0, pady=0)
        self.output_folder = tk.Label(self.output_frame, text="Select a folder", font=("Arial", 8), background="white",
                                      height=2, width=30)
        self.output_folder.pack(side="left", anchor="nw", padx=5, pady=5)
        self.select_output_folder = tk.Button(self.output_frame, width=10, height=1, text="Open",
                                              command=self.select_out_folder)
        self.select_output_folder.pack(side="right", anchor="se", padx=5, pady=(5, 5))

        self.root.mainloop()

    def select_file(self):
        # Open a file selection window and return the selected file path
        filepath = ""
        filepath = filedialog.askopenfilename()
        if filepath != "":
            if filepath[-4:] == ".smr" or filepath[-5:] == ".dill":
                self.input_file_name.config(text=filepath.split("/")[-1])
                self.input_path = filepath
                self.selected_input = True
                self.input_type = "file"
                self.input_files = []
                self.input_name = filepath.split("/")[-1]
            else:
                messagebox.showerror("Error", "Please choose a file of type .smr or .dill")

    def select_folder(self):
        folder_path = ""
        folder_path = filedialog.askdirectory()
        if folder_path != "":
            self.input_files = []
            at_least_one = False
            for item in os.listdir(folder_path):
                filepath = os.path.join(folder_path, item)
                if os.path.isfile(filepath):
                    if filepath[-4:] == ".smr" or filepath[-5:] == ".dill":
                        self.input_files.append(filepath)
                        at_least_one = True

            if at_least_one:
                self.selected_input = True
                self.input_path = folder_path
                self.input_type = "folder"
                self.input_file_name.config(text=folder_path.split("/")[-1])
                self.input_name = folder_path.split("/")[-1]
            else:
                messagebox.showerror("Error", "Selected folder contains no files of the correct format (.smr/.dill)")

    def select_out_folder(self):
        folder_path = ""
        folder_path = filedialog.askdirectory()
        if folder_path != "":
            if self.selected_input:

                if self.input_type == "file":
                    name_exists = False
                    input_name = os.path.splitext(self.input_name)[0]
                    for item in os.listdir(folder_path):
                        if os.path.splitext(item)[0] == input_name and os.path.splitext(item)[1] == '.ino':
                            name_exists = True
                            break

                    if name_exists:
                        messagebox.showerror("Error", "Selected output folder already contains a file with the name: " +
                                             input_name + ".ino")
                    else:
                        self.selected_output = True
                        self.output_folder_path = folder_path
                        self.output_folder.config(text=folder_path.split("/")[-1])

                elif self.input_type == "folder":
                    name_exists = False
                    for item in os.listdir(folder_path):
                        if name_exists:
                            break
                        for in_file in self.input_files:
                            if os.path.splitext(item)[0] == in_file.split("/") and os.path.splitext(item)[1] == '.ino':
                                name_exists = True
                                break
                    if name_exists:
                        messagebox.showerror("Error", "Selected output folder contains a file that will have the"
                                                      " same name as one of the files to be generated")
                    else:
                        self.selected_output = True
                        self.output_folder_path = folder_path
                        self.output_folder.config(text=folder_path.split("/")[-1])
            else:
                self.selected_output = True
                self.output_folder_path = folder_path
                self.output_folder.config(text=folder_path.split("/")[-1])

    def generate(self):
        ok_to_gen = True
        if self.selected_input and self.selected_output:
            if self.input_type == "file":
                input_name = os.path.splitext(self.input_name)[0]
                for item in os.listdir(self.output_folder_path):
                    if os.path.splitext(item)[0] == input_name and os.path.splitext(item)[1] == '.ino':
                        ok_to_gen = False
                        messagebox.showerror("Error", "Selected output folder already contains a file with the name: " +
                                             input_name + ".ino")
                        break

            elif self.input_type == "folder":
                name_exists = False
                for item in os.listdir(self.output_folder_path):
                    if name_exists:
                        break
                    for in_file in self.input_files:
                        if os.path.splitext(item)[0] == in_file.split("/") and os.path.splitext(item)[1] == '.ino':
                            name_exists = True
                            break
                if name_exists:
                    ok_to_gen = False
                    messagebox.showerror("Error", "Selected output folder contains a file that will have the"
                                                  " same name as one of the files to be generated")

            if ok_to_gen:
                input_file_type = ""
                if self.input_type == "file":
                    if self.input_path[-4:] == ".smr":
                        input_file_type = "smr"
                    else:
                        input_file_type = "dill"

                    compiler1 = compiler.Compiler(self.input_path, self.input_name, self.output_folder_path,
                                                  input_file_type)
                    self.progress_bar["value"] = 20
                    compiler1.low_pass_filter_normalise()
                    self.progress_bar["value"] = 40
                    compiler1.gen_lines()
                    self.progress_bar["value"] = 60
                    compiler1.gen_arduino2()
                    self.progress_bar["value"] = 80
                    compiler1.save_to_file()
                    self.progress_bar["value"] = 100
                    self.progress_frame_label.config(text="Success! Click anywhere to reset")
                    self.generate_button.config(state="disabled")
                    self.select_file.config(state="disabled")
                    self.select_folder.config(state="disabled")
                    self.select_output_folder.config(state="disabled")
                    self.root.bind("<Button-1>", self.reset)
                else:
                    current_value = 0
                    bar_increment = round(5/(100/(len(self.input_files))), 5)

                    for file in self.input_files:
                        if file[-4:] == ".smr":
                            input_file_type = "smr"
                        else:
                            input_file_type = "dill"
                        compiler1 = compiler.Compiler(self.input_path, self.input_name, self.output_folder_path,
                                                      input_file_type)
                        current_value = current_value + bar_increment
                        self.progress_bar["value"] = current_value
                        compiler1.low_pass_filter_normalise()
                        current_value = current_value + bar_increment
                        self.progress_bar["value"] = current_value
                        compiler1.gen_lines()
                        current_value = current_value + bar_increment
                        self.progress_bar["value"] = current_value
                        compiler1.gen_arduino2()
                        current_value = current_value + bar_increment
                        self.progress_bar["value"] = current_value
                        compiler1.save_to_file()
                        current_value = current_value + bar_increment
                        self.progress_bar["value"] = current_value

                    self.progress_bar["value"] = 100
                    self.progress_frame_label.config(text="Success! Click anywhere to reset")
        else:
            messagebox.showerror("Error", "Please select an input and destination folder")

    def reset(self, event):

        self.selected_input = False
        self.selected_output = False
        self.input_type = None
        self.input_files = []
        self.input_name = None
        self.input_path = None
        self.output_folder_path = None
        self.progress_frame_label.config(text="Progress")
        self.input_file_name.config(text="Select a file/folder")
        self.output_folder.config(text="Select a folder")
        self.progress_bar["value"] = 0
        self.generate_button.config(state="normal")
        self.select_file.config(state="normal")
        self.select_folder.config(state="normal")
        self.select_output_folder.config(state="normal")
        self.root.unbind("<Button-1>")


gui1 = GUI()

