#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
import logging
import hashlib
from datetime import datetime
import json
import pandas as pd  # For Excel reading and analysis
import os
import webbrowser

# -----------------------------------------------------------------------------
# CONFIGURATION DU LOGGING
# -----------------------------------------------------------------------------
logging.basicConfig(
    filename="company_app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------------------------------------------------------
# FONCTION DE HACHAGE DES MOTS DE PASSE
# -----------------------------------------------------------------------------
def hash_password(password):
    """Retourne le hachage SHA-256 du mot de passe donné."""
    return hashlib.sha256(password.encode()).hexdigest()

# -----------------------------------------------------------------------------
# BASE DE DONNÉES DES UTILISATEURS : Administrateur et Employé
# -----------------------------------------------------------------------------
users = {
    "admin": {"password": hash_password("admin123"), "role": "admin"},
    "employee": {"password": hash_password("emp456"), "role": "employee"}
}

# -----------------------------------------------------------------------------
# CLASSE APPLICATION : Ultimate Company App (Version Française)
# -----------------------------------------------------------------------------
class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ultimate Company App")
        self.geometry("900x650")
        self.current_user = None
        self.role = None  # "admin" ou "employee"
        # Données en mémoire
        self.inventory_data = {}       # {catégorie: [ {"name": nom, "price": prix}, ... ]}
        self.clients_list = []         # [ {"name": nom, "purchases": montant}, ... ]
        self.login_events = []         # [ {"user": utilisateur, "time": heure, "spent": dépensé}, ... ]
        self.orders = []               # Commandes
        self.suppliers = []            # Fournisseurs
        self.projects = []             # Projets
        self.announcements = []        # Annonces
        self.shifts = []               # Quarts de travail
        self.expenses = []             # Dépenses
        # New data lists for extra functions:
        self.feedbacks = []            # Pour recueillir les feedbacks des utilisateurs
        self.tasks = []                # Pour les tâches à assigner

        # Paramètres et configuration
        self.settings = {
            "company_name": "Ultimate Company App",
            "theme_color": "lightgray",
            "enable_notifications": True,
            "auto_logout_time": 15  # minutes
        }
        # Timer d'inactivité pour l'auto-déconnexion
        self.inactivity_timer = None

        # Interface Frames
        self.start_frame = None
        self.login_frame = None
        self.main_menu_frame = None
        self.nav_frame = None
        self.content_frame = None
        self.status_bar = None

        # Quitter avec confirmation
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ------------------------------------------------------------------------------
    # Méthode pour lancer la version HTML du dashboard
    # ------------------------------------------------------------------------------
    def launch_html_dashboard(self):
        # Construct the full path to the HTML file:
        # Change according to your file system. Here it assumes the file "html version.html" is in "~/Desktop/goat/"
        html_file = os.path.join(os.path.expanduser("~"), "Desktop", "goat", "html version.html")
        if not os.path.exists(html_file):
            messagebox.showerror("Erreur", f"Le fichier HTML n'existe pas : {html_file}")
            return
        # Open the file in the default browser
        webbrowser.open("file:///" + html_file)
        logging.info(f"{self.current_user} a lancé la version HTML du dashboard depuis : {html_file}")

    # ------------------------------------------------------------------------------
    # Méthodes de stockage persistant (sauvegarder / charger les données)
    # ------------------------------------------------------------------------------
    def save_data(self):
        data = {
            "inventory_data": self.inventory_data,
            "clients_list": self.clients_list,
            "login_events": self.login_events,
            "orders": self.orders,
            "suppliers": self.suppliers,
            "projects": self.projects,
            "announcements": self.announcements,
            "shifts": self.shifts,
            "expenses": self.expenses,
            "settings": self.settings,
            "feedbacks": self.feedbacks,
            "tasks": self.tasks
        }
        try:
            with open("company_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Succès", "Données sauvegardées.")
            logging.info("Données sauvegardées dans company_data.json.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")

    def load_data(self):
        try:
            with open("company_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            self.inventory_data = data.get("inventory_data", {})
            self.clients_list = data.get("clients_list", [])
            self.login_events = data.get("login_events", [])
            self.orders = data.get("orders", [])
            self.suppliers = data.get("suppliers", [])
            self.projects = data.get("projects", [])
            self.announcements = data.get("announcements", [])
            self.shifts = data.get("shifts", [])
            self.expenses = data.get("expenses", [])
            self.settings = data.get("settings", self.settings)
            self.feedbacks = data.get("feedbacks", [])
            self.tasks = data.get("tasks", [])
            messagebox.showinfo("Succès", "Données chargées.")
            logging.info("Données chargées depuis company_data.json.")
            if self.content_frame:
                self.clear_content_frame()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données: {e}")

    # ------------------------------------------------------------------------------
    # Auto‑déconnexion (inactivité)
    # ------------------------------------------------------------------------------
    def setup_inactivity_timer(self):
        self.reset_logout_timer()
        self.bind_all("<Any-KeyPress>", self.reset_logout_timer)
        self.bind_all("<Any-Button>", self.reset_logout_timer)

    def reset_logout_timer(self, event=None):
        if self.inactivity_timer:
            self.after_cancel(self.inactivity_timer)
        auto_logout_ms = self.settings.get("auto_logout_time", 15) * 60000
        self.inactivity_timer = self.after(auto_logout_ms, self.auto_logout)

    def auto_logout(self):
        messagebox.showinfo("Déconnexion automatique", "Vous avez été déconnecté pour cause d'inactivité.")
        self.logout()

    # ------------------------------------------------------------------------------
    # Interface de démarrage : choix d'accès
    # ------------------------------------------------------------------------------
    def create_start_frame(self):
        self.start_frame = tk.Frame(self)
        self.start_frame.pack(fill="both", expand=True)
        tk.Label(self.start_frame, text="Bienvenue", font=("Arial", 24)).pack(pady=20)
        tk.Label(self.start_frame, text="Choisissez votre mode d'accès :", font=("Arial", 16)).pack(pady=10)
        btn_frame = tk.Frame(self.start_frame)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Accès Employé", font=("Arial", 14), width=15,
                  command=self.employee_access).pack(side="left", padx=20)
        tk.Button(btn_frame, text="Accès Administrateur", font=("Arial", 14), width=15,
                  command=self.admin_access).pack(side="left", padx=20)

    # ------------------------------------------------------------------------------
    # Méthodes d’accès (employé et administrateur)
    # ------------------------------------------------------------------------------
    def employee_access(self):
        emp_username = simpledialog.askstring("Accès Employé", "Saisissez votre nom d'utilisateur :")
        if not emp_username:
            emp_username = "employé"
        self.current_user = emp_username
        self.role = "employee"
        self.record_login_event()
        logging.info(f"L'employé '{self.current_user}' s'est connecté sans mot de passe.")
        self.start_frame.destroy()
        self.update_idletasks()  # Force le rafraîchissement de l'UI
        self.create_main_menu_frame()

    def admin_access(self):
        self.start_frame.destroy()
        self.create_login_frame()

    def create_login_frame(self):
        self.login_frame = tk.Frame(self)
        self.login_frame.pack(fill="both", expand=True)
        tk.Label(self.login_frame, text="Connexion Administrateur", font=("Arial", 24)).pack(pady=20)
        tk.Label(self.login_frame, text="Nom d'utilisateur :").pack(pady=5)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack(pady=5)
        tk.Label(self.login_frame, text="Mot de passe :").pack(pady=5)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.pack(pady=5)
        tk.Button(self.login_frame, text="Connexion", command=self.check_admin_login).pack(pady=20)

    def check_admin_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if username in users:
            user_data = users[username]
            if user_data["role"] != "admin":
                messagebox.showerror("Erreur", "Seuls les administrateurs sont autorisés ici.")
                logging.warning(f"Tentative d'accès admin par un non-admin : {username}")
                return
            if user_data["password"] != hash_password(password):
                messagebox.showerror("Erreur", "Identifiants invalides.")
                logging.warning(f"Échec de connexion admin pour : {username}")
                return
            self.current_user = username
            self.role = "admin"
            self.record_login_event()
            logging.info(f"L'administrateur '{username}' s'est connecté avec succès.")
            self.login_frame.destroy()
            self.update_idletasks()  # Rafraîchit l'interface
            self.create_main_menu_frame()
        else:
            messagebox.showerror("Erreur", "Identifiants invalides.")
            logging.warning(f"Tentative de connexion admin avec un nom inconnu : {username}")

    def record_login_event(self):
        event = {
            "user": self.current_user,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "spent": 0
        }
        self.login_events.append(event)
        logging.info(f"Enregistrement de connexion : {event}")

    # ------------------------------------------------------------------------------
    # Méthode de fermeture avec confirmation
    # ------------------------------------------------------------------------------
    def on_closing(self):
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter ?"):
            self.destroy()

    # ------------------------------------------------------------------------------
    # Création du menu principal et navigation
    # ------------------------------------------------------------------------------
    def create_main_menu_frame(self):
        self.prepare_data()  # Initialise l’inventaire si nécessaire
        self.main_menu_frame = tk.Frame(self)
        self.main_menu_frame.pack(fill="both", expand=True)
        # Navigation à gauche
        self.nav_frame = tk.Frame(self.main_menu_frame, width=200, bg=self.settings["theme_color"])
        self.nav_frame.pack(side="left", fill="y")
        # Zone de contenu à droite
        self.content_frame = tk.Frame(self.main_menu_frame)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Définition des boutons de navigation
        nav_buttons = [
            ("Tableau de Bord", self.show_dashboard),
            ("Inventaire", self.show_inventory),
            ("Liste des Clients", self.show_clients_list),
            ("Liste des Employés", self.show_employees_list),
            ("Commandes", self.show_orders),
            ("Fournisseurs", self.show_suppliers),
            ("Projets", self.show_projects),
            ("Annonces", self.show_announcements),
            ("Planification", self.show_shift_scheduling),
            ("Tableau Financier", self.show_financial_dashboard),
            ("Rapports", self.show_reports)
        ]
        # Pour les employés
        if self.role == "employee":
            nav_buttons.insert(1, ("Mon Profil", self.show_profile))
        # Pour les administrateurs
        elif self.role == "admin":
            nav_buttons.append(("Paramètres", self.show_settings))
        
        # Nouveaux boutons complémentaires
        nav_buttons.append(("Feedback", self.show_feedback))
        nav_buttons.append(("Mes Tâches", self.show_tasks))
        nav_buttons.append(("Analyse Excel", self.show_analysis))  # Remplace le module Calendrier
        nav_buttons.append(("Exporter", self.show_export_options))
        nav_buttons.append(("Calculatrice", self.show_calculator))  # <-- New Calculatrice button
        
        for (text, cmd) in nav_buttons:
            tk.Button(self.nav_frame, text=text, command=cmd, width=20).pack(pady=5, padx=5)
            
        # Bouton de déconnexion
        tk.Button(self.nav_frame, text="Déconnexion", command=self.logout, width=20, bg="salmon")\
            .pack(side="bottom", pady=10)
        # Barre d'état
        self.status_bar = tk.Label(self.main_menu_frame, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side="bottom", fill="x")
        self.update_status_bar()
        self.setup_inactivity_timer()
        self.show_dashboard()

    def update_status_bar(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_text = f"Connecté en tant que : {self.current_user}  |  Heure actuelle : {now}"
        self.status_bar.config(text=status_text)
        self.status_bar.after(1000, self.update_status_bar)

    def prepare_data(self):
        if not self.inventory_data:
            categories = [
                "E36 : Matériaux Technologiques", "O15 : Fournitures de Bureau", "F58 : Mobilier et Installations",
                "I29 : Équipements Industriels", "C12 : Électronique Grand Public", "A04 : Vêtements et Accessoires",
                "B07 : Livres et Magazines", "H11 : Outils et Quincaillerie", "T22 : Jouets et Jeux",
                "G31 : Épicerie et Alimentation", "P44 : Produits Pharmaceutiques", "M66 : Instruments de Musique",
                "L55 : Éclairage et Équipements Électriques", "F20 : Alimentation et Boissons", "S33 : Matériel Sportif",
                "A77 : Pièces Automobiles", "W88 : Technologies Portables", "D99 : Accessoires Numériques",
                "R50 : Produits Écologiques", "L88 : Biens de Luxe", "M21 : Fournitures Médicales",
                "CH01 : Produits pour Enfants", "PH02 : Fournitures pour Animaux", "AR03 : Matériel d'Art et Artisanat",
                "TR04 : Accessoires de Voyage"
            ]
            self.inventory_data = {cat: [] for cat in categories}

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------------------
    # NEW: Module Analyse Excel (remplace Calendrier)
    # ------------------------------------------------------------------------------
    def show_analysis(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Analyse de Fichier Excel", font=("Arial", 16)).pack(pady=10)
        file_path = filedialog.askopenfilename(
            title="Importer un fichier Excel",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if not file_path:
            return
        
        try:
            excel_data = pd.read_excel(file_path, sheet_name=None)
            analysis_text = f"Analyse du fichier : {file_path}\n\n"
            for sheet_name, df in excel_data.items():
                analysis_text += f"Feuille: {sheet_name}\n"
                analysis_text += f"  Nombre de lignes: {len(df)}\n"
                analysis_text += f"  Nombre de colonnes: {len(df.columns)}\n"
                analysis_text += f"  Colonnes: {', '.join(df.columns.astype(str))}\n"
                for col in df.columns:
                    dtype = df[col].dtype
                    non_null = df[col].count()
                    sample_values = df[col].dropna().unique()[:5].tolist()
                    analysis_text += f"    '{col}': type {dtype}, non-null: {non_null}, exemples: {sample_values}\n"
                analysis_text += "\n"
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'analyse : {e}")
            logging.error(f"Erreur lors de l'analyse du fichier Excel '{file_path}': {e}")
            return

        text_widget = tk.Text(self.content_frame, wrap="word", font=("Arial", 12))
        text_widget.insert("1.0", analysis_text)
        text_widget.config(state="disabled")
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)

    # ------------------------------------------------------------------------------
    # NEW: Module Calculatrice
    # ------------------------------------------------------------------------------
    def show_calculator(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Calculatrice", font=("Arial", 16)).pack(pady=10)
        
        calculator_frame = tk.Frame(self.content_frame)
        calculator_frame.pack(pady=10)
        
        # Display widget for the calculator
        display = tk.Entry(calculator_frame, font=("Arial", 16), width=20, borderwidth=2, relief="sunken")
        display.grid(row=0, column=0, columnspan=4, padx=5, pady=5)
        
        # Function to handle button clicks
        def on_button_click(value):
            if value == "C":
                display.delete(0, tk.END)
            elif value == "=":
                try:
                    # Evaluate the expression in the display; only arithmetic operators are allowed.
                    expression = display.get()
                    result = eval(expression)
                    display.delete(0, tk.END)
                    display.insert(tk.END, str(result))
                except Exception as e:
                    messagebox.showerror("Erreur", f"Expression invalide: {e}")
            else:
                display.insert(tk.END, value)
        
        # List of buttons with their positions (row, column)
        buttons = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("C", 4, 2), ("+", 4, 3),
            ("(", 5, 0), (")", 5, 1), ("%", 5, 2), ("=", 5, 3)
        ]
        
        # Create and position the buttons in the grid
        for (text, row, col) in buttons:
            btn = tk.Button(calculator_frame,
                            text=text,
                            width=5,
                            height=2,
                            font=("Arial", 14),
                            command=lambda val=text: on_button_click(val))
            btn.grid(row=row, column=col, padx=3, pady=3)

    # ------------------------------------------------------------------------------
    # Module Export Options (reste inchangé)
    # ------------------------------------------------------------------------------
    def show_export_options(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Options d'Export", font=("Arial", 16)).pack(pady=10)
        export_frame = tk.Frame(self.content_frame)
        export_frame.pack(pady=10)
        tk.Label(export_frame, text="Sélectionnez les données à exporter :")\
          .grid(row=0, column=0, padx=5, pady=5, sticky="w")
        data_options = ["Inventaire", "Clients", "Commandes", "Fournisseurs", "Projets", 
                        "Annonces", "Quarts de travail", "Dépenses", "Feedback", "Tâches"]
        self.export_data_var = tk.StringVar(value=data_options[0])
        ttk.Combobox(export_frame, textvariable=self.export_data_var, values=data_options, state="readonly")\
          .grid(row=0, column=1, padx=5, pady=5)
        tk.Label(export_frame, text="Sélectionnez le format d'export :")\
          .grid(row=1, column=0, padx=5, pady=5, sticky="w")
        export_formats = ["JSON", "CSV", "Excel", "PDF"]
        self.export_format_var = tk.StringVar(value=export_formats[0])
        ttk.Combobox(export_frame, textvariable=self.export_format_var, values=export_formats, state="readonly")\
          .grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self.content_frame, text="Exporter", command=self.export_data)\
          .pack(pady=10)

    def export_data(self):
        selected_data = self.export_data_var.get()
        selected_format = self.export_format_var.get()
        export_extensions = {"JSON": ".json", "CSV": ".csv", "Excel": ".xlsx", "PDF": ".pdf"}
        file_ext = export_extensions.get(selected_format, ".txt")
        file_path = filedialog.asksaveasfilename(defaultextension=file_ext,
                                                 filetypes=[(f"{selected_format} Files", f"*{file_ext}")])
        if not file_path:
            return
        data_to_export = None
        if selected_data == "Inventaire":
            data_to_export = self.inventory_data
        elif selected_data == "Clients":
            data_to_export = self.clients_list
        elif selected_data == "Commandes":
            data_to_export = self.orders
        elif selected_data == "Fournisseurs":
            data_to_export = self.suppliers
        elif selected_data == "Projets":
            data_to_export = self.projects
        elif selected_data == "Annonces":
            data_to_export = self.announcements
        elif selected_data == "Quarts de travail":
            data_to_export = self.shifts
        elif selected_data == "Dépenses":
            data_to_export = self.expenses
        elif selected_data == "Feedback":
            data_to_export = self.feedbacks
        elif selected_data == "Tâches":
            data_to_export = self.tasks
        else:
            data_to_export = {}

        try:
            if selected_format == "JSON":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data_to_export, f, indent=4)
            elif selected_format == "CSV":
                import csv
                if isinstance(data_to_export, dict):
                    if selected_data == "Inventaire":
                        rows = []
                        for cat, products in data_to_export.items():
                            for prod in products:
                                row = {"Catégorie": cat, "Nom": prod.get("name", ""), "Prix": prod.get("price", "")}
                                rows.append(row)
                        if rows:
                            with open(file_path, "w", newline='', encoding="utf-8") as f:
                                writer = csv.DictWriter(f, fieldnames=["Catégorie", "Nom", "Prix"])
                                writer.writeheader()
                                writer.writerows(rows)
                    else:
                        with open(file_path, "w", newline='', encoding="utf-8") as f:
                            writer = csv.writer(f)
                            for key, value in data_to_export.items():
                                writer.writerow([key, value])
                elif isinstance(data_to_export, list):
                    if data_to_export and isinstance(data_to_export[0], dict):
                        keys = list(data_to_export[0].keys())
                        with open(file_path, "w", newline='', encoding="utf-8") as f:
                            writer = csv.DictWriter(f, fieldnames=keys)
                            writer.writeheader()
                            writer.writerows(data_to_export)
                    else:
                        with open(file_path, "w", newline='', encoding="utf-8") as f:
                            writer = csv.writer(f)
                            for item in data_to_export:
                                writer.writerow([item])
                else:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(str(data_to_export))
            elif selected_format == "Excel":
                try:
                    from openpyxl import Workbook
                except ImportError:
                    messagebox.showerror("Erreur", "Le module openpyxl est requis pour l'export Excel.")
                    return
                wb = Workbook()
                ws = wb.active
                if isinstance(data_to_export, list) and data_to_export and isinstance(data_to_export[0], dict):
                    headers = list(data_to_export[0].keys())
                    ws.append(headers)
                    for row in data_to_export:
                        ws.append([row.get(header, "") for header in headers])
                elif isinstance(data_to_export, dict):
                    if selected_data == "Inventaire":
                        ws.append(["Catégorie", "Nom", "Prix"])
                        for cat, products in data_to_export.items():
                            for prod in products:
                                ws.append([cat, prod.get("name", ""), prod.get("price", "")])
                    else:
                        ws.append(["Clé", "Valeur"])
                        for key, value in data_to_export.items():
                            ws.append([key, str(value)])
                else:
                    ws.append(["Données"])
                    ws.append([str(data_to_export)])
                wb.save(file_path)
            elif selected_format == "PDF":
                try:
                    from fpdf import FPDF
                except ImportError:
                    messagebox.showerror("Erreur", "Le module fpdf est requis pour l'export PDF.")
                    return
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                if isinstance(data_to_export, dict) or isinstance(data_to_export, list):
                    text = json.dumps(data_to_export, indent=4, ensure_ascii=False)
                else:
                    text = str(data_to_export)
                for line in text.splitlines():
                    pdf.cell(0, 10, txt=line, ln=1)
                pdf.output(file_path)
            messagebox.showinfo("Succès", f"Données exportées avec succès vers {file_path}")
            logging.info(f"{self.current_user} a exporté {selected_data} en {selected_format} vers {file_path}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")

    # ------------------------------------------------------------------------------
    # Modules restants : Dashboard, Inventaire, Clients, Commandes, etc.
    # ------------------------------------------------------------------------------
    def show_dashboard(self):
        self.clear_content_frame()
        dashboard_frame = tk.Frame(self.content_frame)
        dashboard_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Welcome message
        welcome_text = f"Bienvenue, {self.current_user}!"
        tk.Label(dashboard_frame, text=welcome_text, font=("Arial", 20, "bold"))\
          .grid(row=0, column=0, columnspan=2, pady=10)
        
        # Calculating key metrics
        inventory_count = sum(len(products) for products in self.inventory_data.values())
        clients_count = len(self.clients_list)
        orders_count = len(self.orders)
        total_expenses = sum(exp["amount"] for exp in self.expenses) if self.expenses else 0
        stats = [
            ("Inventaire Total", inventory_count),
            ("Nombre de Clients", clients_count),
            ("Nombre de Commandes", orders_count),
            ("Dépenses Totales", f"{total_expenses:.2f}€")
        ]
        
        # Creating stat panels in a grid layout
        for idx, (label_text, value) in enumerate(stats):
            row = 1 + idx // 2
            col = idx % 2
            frame = tk.Frame(dashboard_frame, bd=2, relief="groove", padx=10, pady=10)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            tk.Label(frame, text=label_text, font=("Arial", 14)).pack()
            tk.Label(frame, text=str(value), font=("Arial", 16, "italic")).pack()
        
        # Announcements section
        ann_frame = tk.Frame(dashboard_frame, bd=2, relief="groove", padx=10, pady=10)
        ann_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        tk.Label(ann_frame, text="Annonces Récentes", font=("Arial", 14, "bold")).pack(pady=5)
        if self.announcements:
            for ann in self.announcements[-3:]:
                ann_text = f"{ann['date']}: {ann['title']} - {ann['content']}"
                tk.Label(ann_frame, text=ann_text, font=("Arial", 12), wraplength=800, justify="left")\
                  .pack(anchor="w", padx=5, pady=2)
        else:
            tk.Label(ann_frame, text="Aucune annonce pour le moment.", font=("Arial", 12)).pack()
        
        # Button to open HTML version of the dashboard
        tk.Button(
            dashboard_frame,
            text="notre version site web",
            command=self.launch_html_dashboard,
            font=("Arial", 14),
            bg="lightblue"
        ).grid(row=4, column=0, columnspan=2, pady=10)

    def show_inventory(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Gestion de l'Inventaire", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.content_frame, text="Sélectionnez une catégorie :").pack(pady=5)
        self.category_var = tk.StringVar()
        self.inventory_categories = list(self.inventory_data.keys())
        self.category_dropdown = ttk.Combobox(self.content_frame, textvariable=self.category_var,
                                              values=self.inventory_categories, state="readonly")
        self.category_dropdown.pack(pady=5)
        self.category_dropdown.bind("<<ComboboxSelected>>", lambda e: self.refresh_inventory_list())
        if self.inventory_categories:
            self.category_var.set(self.inventory_categories[0])
        tk.Label(self.content_frame, text="Nom du produit :").pack(pady=5)
        self.prod_name_entry = tk.Entry(self.content_frame)
        self.prod_name_entry.pack(pady=5)
        tk.Label(self.content_frame, text="Prix :").pack(pady=5)
        self.price_entry = tk.Entry(self.content_frame)
        self.price_entry.pack(pady=5)
        tk.Button(self.content_frame, text="Ajouter le produit", command=self.add_product)\
          .pack(pady=5)
        if self.role == "admin":
            tk.Button(self.content_frame, text="Modifier le produit", command=self.modify_product)\
              .pack(pady=5)
            tk.Button(self.content_frame, text="Supprimer le produit", command=self.delete_product)\
              .pack(pady=5)
        search_frame = tk.Frame(self.content_frame)
        search_frame.pack(pady=5)
        tk.Label(search_frame, text="Rechercher :").pack(side="left")
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side="left", padx=5)
        tk.Button(search_frame, text="Rechercher", command=self.search_product)\
          .pack(side="left", padx=5)
        tk.Button(search_frame, text="Réinitialiser", command=self.refresh_inventory_list)\
          .pack(side="left", padx=5)
        tk.Label(self.content_frame, text="Produits :").pack(pady=5)
        self.products_listbox = tk.Listbox(self.content_frame, width=60)
        self.products_listbox.pack(pady=5)
        self.refresh_inventory_list()

    def add_product(self):
        categorie = self.category_var.get()
        nom = self.prod_name_entry.get().strip()
        prix = self.price_entry.get().strip()
        if not nom or not prix:
            messagebox.showerror("Erreur", "Veuillez fournir le nom et le prix du produit.")
            return
        try:
            prix_val = float(prix)
        except ValueError:
            messagebox.showerror("Erreur", "Format de prix invalide.")
            return
        self.inventory_data.setdefault(categorie, []).append({"name": nom, "price": prix_val})
        messagebox.showinfo("Succès", f"Produit '{nom}' ajouté dans {categorie}.")
        logging.info(f"{self.current_user} a ajouté '{nom}' dans '{categorie}' à {prix_val}€.")
        self.refresh_inventory_list()

    def refresh_inventory_list(self):
        self.products_listbox.delete(0, tk.END)
        categorie = self.category_var.get()
        for idx, prod in enumerate(self.inventory_data.get(categorie, [])):
            self.products_listbox.insert(tk.END, f"{idx+1}. {prod['name']} - {prod['price']:.2f}€")

    def modify_product(self):
        selection = self.products_listbox.curselection()
        if not selection:
            messagebox.showerror("Erreur", "Sélectionnez un produit à modifier.")
            return
        idx = selection[0]
        categorie = self.category_var.get()
        prod = self.inventory_data[categorie][idx]
        nouveau_nom = simpledialog.askstring("Modifier le produit", "Nouveau nom :", initialvalue=prod["name"])
        if not nouveau_nom:
            return
        nouveau_prix = simpledialog.askstring("Modifier le produit", "Nouveau prix :", initialvalue=str(prod["price"]))
        if not nouveau_prix:
            return
        try:
            nouveau_prix_val = float(nouveau_prix)
        except ValueError:
            messagebox.showerror("Erreur", "Prix invalide.")
            return
        self.inventory_data[categorie][idx] = {"name": nouveau_nom.strip(), "price": nouveau_prix_val}
        messagebox.showinfo("Succès", "Produit modifié.")
        logging.info(f"{self.current_user} a modifié le produit à '{nouveau_nom}' à {nouveau_prix_val}€.")
        self.refresh_inventory_list()

    def delete_product(self):
        selection = self.products_listbox.curselection()
        if not selection:
            messagebox.showerror("Erreur", "Sélectionnez un produit à supprimer.")
            return
        idx = selection[0]
        categorie = self.category_var.get()
        prod = self.inventory_data[categorie][idx]
        if messagebox.askyesno("Confirmer", f"Supprimer '{prod['name']}' ?"):
            del self.inventory_data[categorie][idx]
            messagebox.showinfo("Succès", "Produit supprimé.")
            logging.info(f"{self.current_user} a supprimé '{prod['name']}' de '{categorie}'.")
            self.refresh_inventory_list()

    def search_product(self):
        mot_cle = self.search_entry.get().strip().lower()
        if not mot_cle:
            messagebox.showerror("Erreur", "Entrez un mot-clé pour la recherche.")
            return
        self.products_listbox.delete(0, tk.END)
        categorie = self.category_var.get()
        for idx, prod in enumerate(self.inventory_data.get(categorie, [])):
            if mot_cle in prod["name"].lower():
                self.products_listbox.insert(tk.END, f"{idx+1}. {prod['name']} - {prod['price']:.2f}€")

    def show_clients_list(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Liste des Clients", font=("Arial", 16)).pack(pady=10)
        columns = ("Nom", "Achats")
        self.clients_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            self.clients_tree.heading(col, text=col)
        self.clients_tree.pack(pady=5, fill="both", expand=True)
        filter_frame = tk.Frame(self.content_frame)
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="Achat minimum :").pack(side="left")
        self.min_purchase_entry = tk.Entry(filter_frame, width=10)
        self.min_purchase_entry.pack(side="left", padx=5)
        tk.Button(filter_frame, text="Filtrer", command=self.filter_clients)\
          .pack(side="left", padx=5)
        tk.Button(filter_frame, text="Réinitialiser", command=self.refresh_clients_list)\
          .pack(side="left", padx=5)
        btn_frame = tk.Frame(self.content_frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Ajouter un client", command=self.add_client)\
          .pack(side="left", padx=5)
        if self.role == "admin":
            tk.Button(btn_frame, text="Supprimer le client", command=self.delete_client)\
              .pack(side="left", padx=5)
        self.refresh_clients_list()

    def add_client(self):
        nom = simpledialog.askstring("Ajouter un client", "Entrez le nom du client :")
        if not nom:
            return
        montant = simpledialog.askstring("Ajouter un client", "Entrez le montant d'achat :")
        try:
            montant_val = float(montant)
        except (ValueError, TypeError):
            messagebox.showerror("Erreur", "Montant d'achat invalide.")
            return
        self.clients_list.append({"name": nom.strip(), "purchases": montant_val})
        messagebox.showinfo("Succès", f"Client '{nom}' ajouté.")
        logging.info(f"{self.current_user} a ajouté le client '{nom}' pour {montant_val}€ d'achat.")
        self.refresh_clients_list()

    def refresh_clients_list(self):
        for row in self.clients_tree.get_children():
            self.clients_tree.delete(row)
        for client in self.clients_list:
            self.clients_tree.insert("", tk.END, values=(client["name"], client["purchases"]))

    def filter_clients(self):
        try:
            min_achat = float(self.min_purchase_entry.get())
        except ValueError:
            messagebox.showerror("Erreur", "Valeur de filtrage invalide.")
            return
        for row in self.clients_tree.get_children():
            self.clients_tree.delete(row)
        for client in self.clients_list:
            if client["purchases"] >= min_achat:
                self.clients_tree.insert("", tk.END, values=(client["name"], client["purchases"]))

    def delete_client(self):
        selected = self.clients_tree.selection()
        if not selected:
            messagebox.showerror("Erreur", "Sélectionnez un client à supprimer.")
            return
        for sel in selected:
            values = self.clients_tree.item(sel, "values")
            nom = values[0]
            self.clients_list = [c for c in self.clients_list if c["name"] != nom]
        messagebox.showinfo("Succès", "Client(s) supprimé(s).")
        logging.info(f"{self.current_user} a supprimé un ou plusieurs clients.")
        self.refresh_clients_list()

    def show_employees_list(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Liste des Employés (Connexions)", font=("Arial", 16))\
          .pack(pady=10)
        columns = ("Utilisateur", "Heure de connexion", "Dépensé")
        self.employees_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            self.employees_tree.heading(col, text=col)
        self.employees_tree.pack(pady=5, fill="both", expand=True)
        if not self.login_events:
            tk.Label(self.content_frame, text="Aucun enregistrement de connexion.",
                     font=("Arial", 14), fg="red").pack(pady=5)
        else:
            for record in self.login_events:
                self.employees_tree.insert("", tk.END, values=(record["user"], record["time"], record["spent"]))
        tk.Button(self.content_frame, text="Résumé des employés", command=self.show_employee_summary)\
          .pack(pady=5)

    def show_employee_summary(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Résumé des Employés", font=("Arial", 16)).pack(pady=10)
        summary = {}
        for record in self.login_events:
            user = record["user"]
            summary[user] = summary.get(user, 0) + 1
        if not summary:
            tk.Label(self.content_frame, text="Aucun enregistrement de connexion.",
                     font=("Arial", 14), fg="red").pack(pady=5)
            return
        columns = ("Utilisateur", "Nombre de connexions")
        summary_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            summary_tree.heading(col, text=col)
        summary_tree.pack(pady=5, fill="both", expand=True)
        for user, count in summary.items():
            summary_tree.insert("", tk.END, values=(user, count))
        tk.Button(self.content_frame, text="Retour aux détails", command=self.show_employees_list)\
          .pack(pady=5)

    def show_orders(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Gestion des Commandes", font=("Arial", 16)).pack(pady=10)
        tk.Button(self.content_frame, text="Ajouter une commande", command=self.add_order)\
          .pack(pady=5)
        columns = ("ID Commande", "Client", "Montant Total", "Date de commande")
        self.orders_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            self.orders_tree.heading(col, text=col)
        self.orders_tree.pack(pady=5, fill="both", expand=True)
        self.refresh_orders()

    def add_order(self):
        client = simpledialog.askstring("Ajouter une commande", "Entrez le nom du client :")
        if not client:
            return
        total = simpledialog.askstring("Ajouter une commande", "Entrez le montant total :")
        try:
            total_val = float(total)
        except:
            messagebox.showerror("Erreur", "Montant invalide.")
            return
        order_id = len(self.orders) + 1
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order = {"order_id": order_id, "client": client.strip(), "total": total_val, "order_date": order_date}
        self.orders.append(order)
        messagebox.showinfo("Succès", "Commande ajoutée avec succès !")
        logging.info(f"{self.current_user} a ajouté la commande {order}.")
        self.refresh_orders()

    def refresh_orders(self):
        for row in self.orders_tree.get_children():
            self.orders_tree.delete(row)
        for order in self.orders:
            self.orders_tree.insert("", tk.END, values=(order["order_id"], order["client"],
                                                         f"{order['total']:.2f}€", order["order_date"]))

    def show_suppliers(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Gestion des Fournisseurs", font=("Arial", 16)).pack(pady=10)
        btn_frame = tk.Frame(self.content_frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Ajouter un fournisseur", command=self.add_supplier)\
          .pack(side="left", padx=5)
        if self.role == "admin":
            tk.Button(btn_frame, text="Modifier un fournisseur", command=self.modify_supplier)\
              .pack(side="left", padx=5)
            tk.Button(btn_frame, text="Supprimer un fournisseur", command=self.delete_supplier)\
              .pack(side="left", padx=5)
        columns = ("Nom", "Contact", "Note")
        self.suppliers_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            self.suppliers_tree.heading(col, text=col)
        self.suppliers_tree.pack(pady=5, fill="both", expand=True)
        self.refresh_suppliers()

    def add_supplier(self):
        nom = simpledialog.askstring("Ajouter un fournisseur", "Nom du fournisseur :")
        if not nom:
            return
        contact = simpledialog.askstring("Ajouter un fournisseur", "Contact :")
        rating = simpledialog.askstring("Ajouter un fournisseur", "Note (1-5) :")
        try:
            rating_val = float(rating)
        except:
            messagebox.showerror("Erreur", "Note invalide.")
            return
        supplier = {"name": nom.strip(), "contact": contact.strip() if contact else "", "rating": rating_val}
        self.suppliers.append(supplier)
        messagebox.showinfo("Succès", "Fournisseur ajouté avec succès !")
        logging.info(f"{self.current_user} a ajouté le fournisseur {supplier}.")
        self.refresh_suppliers()

    def refresh_suppliers(self):
        for row in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(row)
        for supp in self.suppliers:
            self.suppliers_tree.insert("", tk.END, values=(supp["name"], supp["contact"], supp["rating"]))

    def modify_supplier(self):
        selected = self.suppliers_tree.selection()
        if not selected:
            messagebox.showerror("Erreur", "Sélectionnez un fournisseur à modifier.")
            return
        item = self.suppliers_tree.item(selected[0])
        nom = item["values"][0]
        for supplier in self.suppliers:
            if supplier["name"] == nom:
                nouveau_nom = simpledialog.askstring("Modifier", "Nouveau nom :", initialvalue=supplier["name"])
                nouveau_contact = simpledialog.askstring("Modifier", "Nouveau contact :", initialvalue=supplier["contact"])
                nouvelle_note = simpledialog.askstring("Modifier", "Nouvelle note (1-5) :", initialvalue=str(supplier["rating"]))
                try:
                    nouvelle_note_val = float(nouvelle_note)
                except:
                    messagebox.showerror("Erreur", "Note invalide.")
                    return
                supplier["name"] = nouveau_nom.strip()
                supplier["contact"] = nouveau_contact.strip() if nouveau_contact else ""
                supplier["rating"] = nouvelle_note_val
                break
        messagebox.showinfo("Succès", "Fournisseur modifié.")
        logging.info(f"L'administrateur {self.current_user} a modifié le fournisseur : {supplier}.")
        self.refresh_suppliers()

    def delete_supplier(self):
        selected = self.suppliers_tree.selection()
        if not selected:
            messagebox.showerror("Erreur", "Sélectionnez un fournisseur à supprimer.")
            return
        item = self.suppliers_tree.item(selected[0])
        nom = item["values"][0]
        self.suppliers = [s for s in self.suppliers if s["name"] != nom]
        messagebox.showinfo("Succès", "Fournisseur supprimé.")
        logging.info(f"{self.current_user} a supprimé le fournisseur '{nom}'.")
        self.refresh_suppliers()

    def show_projects(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Gestion des Projets", font=("Arial", 16)).pack(pady=10)
        btn_frame = tk.Frame(self.content_frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Ajouter un projet", command=self.add_project)\
          .pack(side="left", padx=5)
        if self.role == "admin":
            tk.Button(btn_frame, text="Modifier un projet", command=self.modify_project)\
              .pack(side="left", padx=5)
            tk.Button(btn_frame, text="Supprimer un projet", command=self.delete_project)\
              .pack(side="left", padx=5)
        columns = ("ID Projet", "Nom", "Date Limite", "Statut", "Assigné à")
        self.projects_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            self.projects_tree.heading(col, text=col)
        self.projects_tree.pack(pady=5, fill="both", expand=True)
        self.refresh_projects()

    def add_project(self):
        nom = simpledialog.askstring("Ajouter un projet", "Nom du projet :")
        if not nom:
            return
        deadline = simpledialog.askstring("Ajouter un projet", "Date limite (AAAA-MM-JJ) :")
        statut = simpledialog.askstring("Ajouter un projet", "Statut (En attente/En cours/Terminé) :")
        assigné = simpledialog.askstring("Ajouter un projet", "Assigné à (nom de l'employé) :")
        project_id = len(self.projects) + 1
        projet = {"project_id": project_id, "name": nom.strip(), "deadline": deadline,
                  "status": statut, "assigned_to": assigné}
        self.projects.append(projet)
        messagebox.showinfo("Succès", "Projet ajouté.")
        logging.info(f"{self.current_user} a ajouté le projet {projet}.")
        self.refresh_projects()

    def refresh_projects(self):
        for row in self.projects_tree.get_children():
            self.projects_tree.delete(row)
        for proj in self.projects:
            self.projects_tree.insert("", tk.END,
                                      values=(proj["project_id"], proj["name"], proj["deadline"], proj["status"], proj["assigned_to"]))

    def modify_project(self):
        selected = self.projects_tree.selection()
        if not selected:
            messagebox.showerror("Erreur", "Sélectionnez un projet à modifier.")
            return
        item = self.projects_tree.item(selected[0])
        proj_id = item["values"][0]
        for proj in self.projects:
            if proj["project_id"] == proj_id:
                nouveau_nom = simpledialog.askstring("Modifier un projet", "Nouveau nom :", initialvalue=proj["name"])
                nouvelle_deadline = simpledialog.askstring("Modifier un projet", "Nouvelle date limite (AAAA-MM-JJ) :", initialvalue=proj["deadline"])
                nouveau_statut = simpledialog.askstring("Modifier un projet", "Nouveau statut :", initialvalue=proj["status"])
                nouveau_assigné = simpledialog.askstring("Modifier un projet", "Assigné à :", initialvalue=proj["assigned_to"])
                proj["name"] = nouveau_nom.strip()
                proj["deadline"] = nouvelle_deadline
                proj["status"] = nouveau_statut
                proj["assigned_to"] = nouveau_assigné
                break
        messagebox.showinfo("Succès", "Projet modifié.")
        logging.info(f"L'administrateur {self.current_user} a modifié le projet {proj}.")
        self.refresh_projects()

    def delete_project(self):
        selected = self.projects_tree.selection()
        if not selected:
            messagebox.showerror("Erreur", "Sélectionnez un projet à supprimer.")
            return
        item = self.projects_tree.item(selected[0])
        proj_id = item["values"][0]
        self.projects = [p for p in self.projects if p["project_id"] != proj_id]
        messagebox.showinfo("Succès", "Projet supprimé.")
        logging.info(f"{self.current_user} a supprimé le projet avec l'ID {proj_id}.")
        self.refresh_projects()

    def show_announcements(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Annonces", font=("Arial", 16)).pack(pady=10)
        if self.role == "admin":
            tk.Button(self.content_frame, text="Ajouter une annonce", command=self.add_announcement)\
              .pack(pady=5)
        columns = ("Titre", "Date", "Contenu")
        self.announcements_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            self.announcements_tree.heading(col, text=col)
        self.announcements_tree.pack(pady=5, fill="both", expand=True)
        self.refresh_announcements()

    def add_announcement(self):
        titre = simpledialog.askstring("Ajouter une annonce", "Titre :")
        if not titre:
            return
        contenu = simpledialog.askstring("Ajouter une annonce", "Contenu :")
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        annonce = {"title": titre.strip(), "content": contenu, "date": date}
        self.announcements.append(annonce)
        messagebox.showinfo("Succès", "Annonce ajoutée.")
        logging.info(f"{self.current_user} a ajouté l'annonce {annonce}.")
        self.refresh_announcements()

    def refresh_announcements(self):
        for row in self.announcements_tree.get_children():
            self.announcements_tree.delete(row)
        for ann in self.announcements:
            self.announcements_tree.insert("", tk.END, values=(ann["title"], ann["date"], ann["content"]))

    def show_shift_scheduling(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Planification des Quarts de Travail", font=("Arial", 16))\
          .pack(pady=10)
        if self.role == "admin":
            tk.Button(self.content_frame, text="Ajouter un quart", command=self.add_shift)\
              .pack(pady=5)
        columns = ("Employé", "Date", "Début", "Fin", "Notes")
        self.shifts_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            self.shifts_tree.heading(col, text=col)
        self.shifts_tree.pack(pady=5, fill="both", expand=True)
        self.refresh_shifts()

    def add_shift(self):
        employe = simpledialog.askstring("Ajouter un quart", "Nom de l'employé :")
        date = simpledialog.askstring("Ajouter un quart", "Date du quart (AAAA-MM-JJ) :")
        debut = simpledialog.askstring("Ajouter un quart", "Heure de début (HH:MM) :")
        fin = simpledialog.askstring("Ajouter un quart", "Heure de fin (HH:MM) :")
        notes = simpledialog.askstring("Ajouter un quart", "Notes :")
        shift = {"employee": employe.strip(), "date": date, "start": debut, "end": fin, "notes": notes}
        self.shifts.append(shift)
        messagebox.showinfo("Succès", "Quart ajouté.")
        logging.info(f"{self.current_user} a ajouté le quart {shift}.")
        self.refresh_shifts()

    def refresh_shifts(self):
        for row in self.shifts_tree.get_children():
            self.shifts_tree.delete(row)
        for s in self.shifts:
            self.shifts_tree.insert("", tk.END, values=(s["employee"], s["date"], s["start"], s["end"], s["notes"]))

    def show_financial_dashboard(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Tableau de bord Financier", font=("Arial", 16))\
          .pack(pady=10)
        tk.Button(self.content_frame, text="Ajouter une dépense", command=self.add_expense)\
          .pack(pady=5)
        total_revenue = sum(order["total"] for order in self.orders)
        order_count = len(self.orders)
        avg_order_val = (total_revenue / order_count) if order_count > 0 else 0
        total_expenses = sum(exp["amount"] for exp in self.expenses) if self.expenses else 0
        net_profit = total_revenue - total_expenses
        report_text = (
            f"Revenu Total : {total_revenue:.2f}€\n"
            f"Nombre de Commandes : {order_count}\n"
            f"Valeur Moyenne par Commande : {avg_order_val:.2f}€\n"
            f"Dépenses Totales : {total_expenses:.2f}€\n"
            f"Profit Net : {net_profit:.2f}€\n"
        )
        tk.Label(self.content_frame, text=report_text, font=("Arial", 14), justify="left")\
          .pack(padx=10, pady=10)
        columns = ("ID Commande", "Client", "Total", "Date")
        self.financial_orders_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        for col in columns:
            self.financial_orders_tree.heading(col, text=col)
        self.financial_orders_tree.pack(pady=5, fill="both", expand=True)
        for order in self.orders:
            self.financial_orders_tree.insert("", tk.END,
                                              values=(order["order_id"], order["client"],
                                                      f"{order['total']:.2f}€", order["order_date"]))

    def add_expense(self):
        objet = simpledialog.askstring("Ajouter une dépense", "Objet de la dépense :")
        montant = simpledialog.askstring("Ajouter une dépense", "Montant de la dépense :")
        try:
            montant_val = float(montant)
        except:
            messagebox.showerror("Erreur", "Montant invalide.")
            return
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        expense = {"purpose": objet, "amount": montant_val, "date": date}
        self.expenses.append(expense)
        messagebox.showinfo("Succès", "Dépense ajoutée.")
        logging.info(f"{self.current_user} a ajouté la dépense {expense}.")
        self.show_financial_dashboard()

    def show_reports(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Rapports", font=("Arial", 16)).pack(pady=10)
        total_products = sum(len(prods) for prods in self.inventory_data.values())
        client_count = len(self.clients_list)
        avg_purchase = (sum(c["purchases"] for c in self.clients_list) / client_count) if client_count > 0 else 0
        login_count = len(self.login_events)
        report_text = (
            f"Total d'articles en inventaire : {total_products}\n"
            f"Nombre de clients : {client_count}\n"
            f"Achat moyen par client : {avg_purchase:.2f}€\n"
            f"Total des enregistrements de connexion : {login_count}\n\n"
            "Inventaire par catégorie :\n"
        )
        for cat, prods in self.inventory_data.items():
            report_text += f"  {cat} : {len(prods)} articles\n"
        tk.Label(self.content_frame, text=report_text, font=("Arial", 14), justify="left")\
          .pack(padx=10, pady=10)

    def show_settings(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Paramètres", font=("Arial", 16)).pack(pady=10)
        company_name_var = tk.StringVar(value=self.settings.get("company_name", "Ultimate Company App"))
        theme_color_var = tk.StringVar(value=self.settings.get("theme_color", "lightgray"))
        enable_notifications_var = tk.BooleanVar(value=self.settings.get("enable_notifications", True))
        auto_logout_time_var = tk.StringVar(value=str(self.settings.get("auto_logout_time", 15)))
        form_frame = tk.Frame(self.content_frame)
        form_frame.pack(pady=10)
        tk.Label(form_frame, text="Nom de l'entreprise :")\
          .grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(form_frame, textvariable=company_name_var)\
          .grid(row=0, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Couleur du thème :")\
          .grid(row=1, column=0, sticky="w", padx=5, pady=5)
        theme_options = ["lightgray", "white", "lightblue", "lightgreen", "lightyellow"]
        theme_dropdown = ttk.Combobox(form_frame, textvariable=theme_color_var,
                                      values=theme_options, state="readonly")
        theme_dropdown.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Activer les notifications :")\
          .grid(row=2, column=0, sticky="w", padx=5, pady=5)
        tk.Checkbutton(form_frame, variable=enable_notifications_var)\
          .grid(row=2, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Temps d'auto-déconnexion (min) :")\
          .grid(row=3, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(form_frame, textvariable=auto_logout_time_var)\
          .grid(row=3, column=1, padx=5, pady=5)
        
        admin_frame = tk.LabelFrame(self.content_frame, text="Options Administrateur", padx=10, pady=10)
        admin_frame.pack(pady=10)
        tk.Button(admin_frame, text="Mettre à jour le mot de passe admin", command=self.update_admin_password)\
          .pack(pady=5)
        tk.Button(admin_frame, text="Effacer les logs de connexion", command=self.clear_login_logs)\
          .pack(pady=5)
        tk.Button(admin_frame, text="Sauvegarder données", command=self.save_data)\
          .pack(pady=5)
        tk.Button(admin_frame, text="Charger données", command=self.load_data)\
          .pack(pady=5)
        
        button_frame = tk.Frame(self.content_frame)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Enregistrer les paramètres", command=lambda: self.save_settings(
            company_name_var.get(), theme_color_var.get(), enable_notifications_var.get(), auto_logout_time_var.get()
        )).pack(side="left", padx=10)
        tk.Button(button_frame, text="Réinitialiser les données", command=self.reset_data)\
          .pack(side="left", padx=10)

    def save_settings(self, company_name, theme_color, enable_notifications, auto_logout_time):
        try:
            auto_logout_time = int(auto_logout_time)
        except ValueError:
            messagebox.showerror("Erreur", "Le temps d'auto-déconnexion doit être un entier.")
            return
        self.settings["company_name"] = company_name
        self.settings["theme_color"] = theme_color
        self.settings["enable_notifications"] = enable_notifications
        self.settings["auto_logout_time"] = auto_logout_time
        self.title(company_name)
        self.nav_frame.config(bg=theme_color)
        messagebox.showinfo("Succès", "Paramètres enregistrés avec succès !")
        self.reset_logout_timer()

    def reset_data(self):
        if messagebox.askyesno("Réinitialiser", "Réinitialiser l'inventaire et la liste des clients ?"):
            self.prepare_data()
            self.clients_list = []
            messagebox.showinfo("Réinitialisation", "Les données ont été réinitialisées.")

    def update_admin_password(self):
        current = simpledialog.askstring("Mettre à jour le mot de passe", "Entrez le mot de passe actuel :", show="*")
        if not current or users["admin"]["password"] != hash_password(current):
            messagebox.showerror("Erreur", "Mot de passe actuel incorrect.")
            return
        new_pass = simpledialog.askstring("Mettre à jour le mot de passe", "Entrez le nouveau mot de passe :", show="*")
        if not new_pass:
            return
        confirm_pass = simpledialog.askstring("Mettre à jour le mot de passe", "Confirmez le nouveau mot de passe :", show="*")
        if new_pass != confirm_pass:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas !")
            return
        users["admin"]["password"] = hash_password(new_pass)
        messagebox.showinfo("Succès", "Mot de passe administrateur mis à jour avec succès !")
        logging.info(f"{self.current_user} a mis à jour le mot de passe admin.")

    def clear_login_logs(self):
        self.login_events = []
        messagebox.showinfo("Succès", "Les logs de connexion ont été effacés.")
        logging.info(f"{self.current_user} a effacé les logs de connexion.")

    def show_profile(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Mon Profil", font=("Arial", 16)).pack(pady=10)
        info_text = f"Utilisateur : {self.current_user}\n"
        user_events = [event for event in self.login_events if event["user"] == self.current_user]
        info_text += f"Nombre de connexions : {len(user_events)}\n"
        tk.Label(self.content_frame, text=info_text, font=("Arial", 14), justify="left")\
          .pack(padx=10, pady=10)

    def show_feedback(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Feedback", font=("Arial", 16)).pack(pady=10)
        feedback_frame = tk.Frame(self.content_frame)
        feedback_frame.pack(fill="both", expand=True, padx=10, pady=10)
        feedback_listbox = tk.Listbox(feedback_frame, width=80, height=10)
        feedback_listbox.pack(pady=5)
        for fb in self.feedbacks:
            feedback_listbox.insert(
                tk.END, f"{fb['time']} - {fb['user']}: {fb['message']}"
            )
        tk.Button(self.content_frame, text="Ajouter Feedback", command=self.add_feedback)\
          .pack(pady=5)

    def add_feedback(self):
        message = simpledialog.askstring("Ajouter Feedback", "Entrez votre feedback :")
        if message:
            fb = {
                "user": self.current_user,
                "message": message,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.feedbacks.append(fb)
            messagebox.showinfo("Succès", "Feedback ajouté.")
            self.show_feedback()

    def show_tasks(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Mes Tâches", font=("Arial", 16)).pack(pady=10)
        tasks_listbox = tk.Listbox(self.content_frame, width=80, height=10)
        tasks_listbox.pack(pady=5)
        for t in self.tasks:
            if self.role == "employee" and t.get("assignee") != self.current_user:
                continue
            tasks_listbox.insert(
                tk.END, f"{t.get('due','N/A')} - {t.get('task')} (Status : {t.get('status','Pending')})"
            )
        tk.Button(self.content_frame, text="Ajouter Tâche", command=self.add_task)\
          .pack(pady=5)

    def add_task(self):
        if self.role != "admin":
            messagebox.showerror("Erreur", "Seul l'administrateur peut ajouter des tâches.")
            return
        task_text = simpledialog.askstring("Ajouter Tâche", "Entrez la description de la tâche :")
        if not task_text:
            return
        assignee = simpledialog.askstring("Ajouter Tâche", "Attribuer à l'employé (nom) :")
        due_date = simpledialog.askstring("Ajouter Tâche", "Date d'échéance (AAAA-MM-JJ) :")
        new_task = {
            "task": task_text,
            "assignee": assignee,
            "due": due_date,
            "status": "Pending"
        }
        self.tasks.append(new_task)
        messagebox.showinfo("Succès", "Tâche ajoutée.")
        self.show_tasks()

    def logout(self):
        if messagebox.askyesno("Déconnexion", "Confirmez-vous la déconnexion ?"):
            logging.info(f"{self.current_user} s'est déconnecté.")
            self.current_user = None
            self.role = None
            if self.inactivity_timer:
                self.after_cancel(self.inactivity_timer)
            self.unbind_all("<Any-KeyPress>")
            self.unbind_all("<Any-Button>")
            self.main_menu_frame.destroy()
            self.create_start_frame()

# -----------------------------------------------------------------------------
# Programme Principal
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = Application()
    app.create_start_frame()
    app.mainloop()
