import customtkinter
import script
from tkinter import filedialog


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gerador de Documentação LLD")

        # Configurar o grid layout (1x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Frame Principal ---
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Título ---
        self.title_label = customtkinter.CTkLabel(self.main_frame, text="Gerador Automático de LLD",
                                                  font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- Campo de Seleção de Tipo ---
        self.type_label = customtkinter.CTkLabel(self.main_frame, text="Tipo de Equipamento:", anchor="w")
        self.type_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="ew")

        device_types = ["WLC9800", "Switch Catalyst", "Meraki", "Fortigate"]
        self.type_combobox = customtkinter.CTkComboBox(self.main_frame, values=device_types,
                                                       command=self.show_options)
        self.type_combobox.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.type_combobox.set("Selecione um tipo...")  # Valor inicial

        # --- Frames para Opções Condicionais ---
        self.cisco_options_frame = customtkinter.CTkFrame(self.main_frame)
        self.meraki_options_frame = customtkinter.CTkFrame(self.main_frame)

        self.setup_cisco_ui()
        self.setup_meraki_ui()

        # --- Botão Gerar ---
        self.generate_button = customtkinter.CTkButton(self.main_frame, text="Gerar", command=self.doc_generator)
        self.generate_button.grid(row=5, column=0, padx=20, pady=20, sticky="ew")

    def setup_cisco_ui(self):
        """ Configura os campos para WLC9800 e Switch Catalyst """
        self.cisco_options_frame.grid_columnconfigure(0, weight=1)

        # Campo Show Tech
        self.show_tech_entry = self.create_file_entry(self.cisco_options_frame, "Arquivo Show Tech:", 0)
        # Campo AP Summary
        self.ap_summary_entry = self.create_file_entry(self.cisco_options_frame, "Arquivo AP Summary:", 1)
        # Campo Template
        self.cisco_template_entry = self.create_file_entry(self.cisco_options_frame, "Arquivo de Template (.docx):", 2,
                                                           "docx")

    def setup_meraki_ui(self):
        """ Configura os campos para Meraki """
        self.meraki_options_frame.grid_columnconfigure(0, weight=1)

        # Campo Token
        self.token_entry = self.create_text_entry(self.meraki_options_frame, "Token da API Meraki:", 0)
        # Campo Organization Name
        self.org_name_entry = self.create_text_entry(self.meraki_options_frame, "Nome da Organização:", 1)
        # Campo Network Name
        self.net_name_entry = self.create_text_entry(self.meraki_options_frame, "Nome da Network:", 2)
        # Campo Template
        self.meraki_template_entry = self.create_file_entry(self.meraki_options_frame, "Arquivo de Template (.docx):",
                                                            3, "docx")

    def create_file_entry(self, parent_frame, label_text, row, file_type="all"):
        """ Função auxiliar para criar um campo de entrada de arquivo com botão """
        label = customtkinter.CTkLabel(parent_frame, text=label_text, anchor="w")
        label.grid(row=row * 2, column=0, padx=20, pady=(10, 0), sticky="ew")

        entry_frame = customtkinter.CTkFrame(parent_frame, fg_color="transparent")
        entry_frame.grid(row=row * 2 + 1, column=0, padx=20, pady=5, sticky="ew")
        entry_frame.grid_columnconfigure(0, weight=1)

        entry = customtkinter.CTkEntry(entry_frame, placeholder_text=f"Caminho para o arquivo...")
        entry.grid(row=0, column=0, sticky="ew")

        button = customtkinter.CTkButton(entry_frame, text="Selecionar...", width=100,
                                         command=lambda e=entry, ft=file_type: self.select_file(e, ft))
        button.grid(row=0, column=1, padx=(10, 0))
        return entry

    def create_text_entry(self, parent_frame, label_text, row):
        """ Função auxiliar para criar um campo de texto simples """
        label = customtkinter.CTkLabel(parent_frame, text=label_text, anchor="w")
        label.grid(row=row * 2, column=0, padx=20, pady=(10, 0), sticky="ew")
        entry = customtkinter.CTkEntry(parent_frame,
                                       placeholder_text=f"Insira o {label_text.lower().replace(':', '')}...")
        entry.grid(row=row * 2 + 1, column=0, padx=20, pady=5, sticky="ew")
        return entry

    def select_file(self, entry_widget, file_type):
        """ Abre o explorador de arquivos e insere o caminho no campo de entrada """
        if file_type == "docx":
            filetypes = [("Documentos Word", "*.docx")]
        else:
            filetypes = [("Todos os arquivos", "*.*")]

        filepath = filedialog.askopenfilename(title="Selecionar arquivo", filetypes=filetypes)
        if filepath:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filepath)

    def show_options(self, choice):
        """ Mostra ou esconde os frames de opções com base na escolha """
        # Primeiro, esconde todos os frames
        self.cisco_options_frame.grid_forget()
        self.meraki_options_frame.grid_forget()

        # Mostra o frame correto
        if choice in ["WLC9800", "Switch Catalyst"]:
            self.cisco_options_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        elif choice == "Meraki":
            self.meraki_options_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

    def doc_generator(self):
        """
        Função executada pelo botão 'Gerar'.
        Coleta todas as informações e as imprime no console.
        """
        get_type = self.type_combobox.get()

        print("=" * 30)
        print("Opções Selecionadas para Geração")
        print("=" * 30)
        print(f"Tipo de Equipamento: {get_type}")

        if get_type in ["WLC9800", "Switch Catalyst"]:
            print(f"  - Arquivo Show Tech: {self.show_tech_entry.get()}")
            print(f"  - Arquivo AP Summary: {self.ap_summary_entry.get()} Ainda não implementado na geração de documentos")
            print(f"  - Arquivo de Template: {self.cisco_template_entry.get()}")
            script.cisco_built_generator(f'{self.show_tech_entry.get()}', f'{self.cisco_template_entry.get()}')

        elif get_type == "Meraki":
            print(f"  - Token da API: {self.token_entry.get()}")
            print(f"  - Nome da Organização: {self.org_name_entry.get()}")
            print(f"  - Nome da Network: {self.net_name_entry.get()}")
            print(f"  - Arquivo de Template: {self.meraki_template_entry.get()}")
        elif get_type == "Fortigate":
            print("  - (Nenhuma opção adicional configurada para Fortigate)")
        else:
            print("  - [AVISO] Nenhum tipo de equipamento válido selecionado.")

        print("=" * 30)


if __name__ == "__main__":
    app = App()
    app.mainloop()