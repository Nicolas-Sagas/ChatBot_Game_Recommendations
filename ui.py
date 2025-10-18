# ui.py (VERSÃO COM CORREÇÃO DE KEYERROR)
import tkinter as tk
from tkinter import scrolledtext, messagebox
import sqlite3 
import hashlib 
from datetime import datetime
import locale
from pathlib import Path
import threading
from queue import Queue, Empty

import services

caminho_base = Path(__file__).resolve().parent

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try: locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except locale.Error: print("Aviso: Locale 'pt_BR' não encontrado.")

THEMES = {
    "dark": { "bg": "#121212", "bg_secondary": "#1E1E1E", "fg": "#00BFFF", "fg_accent": "#E0E0E0", "game_title": "#FFD700", "btn_cta_bg": "#F92672", "btn_cta_fg": "white", "btn_primary_bg": "#007ACC", "btn_primary_fg": "white", "btn_secondary_bg": "#555555", "btn_secondary_fg": "white" },
    "light": { "bg": "#F5F5F5", "bg_secondary": "#FFFFFF", "fg": "#007ACC", "fg_accent": "#2F4F4F", "game_title": "#B8860B", "btn_cta_bg": "#FF7F50", "btn_cta_fg": "white", "btn_primary_bg": "#007ACC", "btn_primary_fg": "white", "btn_secondary_bg": "#AAAAAA", "btn_secondary_fg": "white" }
}
FONTS = { "main": ("Consolas", 11), "main_bold": ("Consolas", 11, "bold"), "title": ("Consolas", 22, "bold"), "subtitle": ("Consolas", 12)}

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatbot de Recomendação de Jogos")
        
        self.current_theme = "dark" 
        self.modelo_ia = services.configurar_e_obter_modelo_ia()
        if self.modelo_ia is None: messagebox.showerror("Erro de API", "Não foi possível configurar o modelo de IA.")

        self.db_conn = self.configurar_banco_de_dados()
        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1); self.container.grid_columnconfigure(0, weight=1)
        
        self.response_queue = Queue()

        self.frames = {}
        for F in (TelaLogin, TelaCadastro, TelaChat, TelaSucesso):
            # <--- ALTERAÇÃO: Usando o nome da classe (string) como chave ---
            frame_name = F.__name__
            frame = F(self.container, self)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.mostrar_tela('TelaLogin') # <--- ALTERAÇÃO: Chamando pela string
        self.aplicar_tema(); self.atualizar_icones_tema() 
        self.processar_respostas_da_fila()

    def processar_respostas_da_fila(self):
        try:
            resposta, tag = self.response_queue.get_nowait()
            chat_frame = self.frames['TelaChat'] # <--- ALTERAÇÃO: Usando string
            chat_frame.is_thinking = False
            chat_frame.texto_conversa.config(state=tk.NORMAL)
            chat_frame.texto_conversa.delete("end-2l linestart", "end-1l lineend")
            chat_frame.adicionar_mensagem(resposta, tag)
        except Empty:
            pass
        finally:
            self.root.after(100, self.processar_respostas_da_fila)

    def configurar_banco_de_dados(self):
        conn = sqlite3.connect(caminho_base / "usuarios.db"); cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha_hash TEXT)")
        conn.commit(); return conn

    def mostrar_tela(self, frame_name): # <--- ALTERAÇÃO: Recebe o nome (string)
        frame = self.frames[frame_name]; frame.tkraise()
        if frame_name == 'TelaChat': self.centralizar_janela(800, 600)
        else: self.centralizar_janela(800, 500)

    def centralizar_janela(self, largura, altura):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (largura // 2); y = (self.root.winfo_screenheight() // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")
    
    def alternar_tema(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"; self.aplicar_tema(); self.atualizar_icones_tema()

    def atualizar_icones_tema(self):
        icone = "☀️" if self.current_theme == "light" else "🌙"
        for frame in self.frames.values():
            if hasattr(frame, 'btn_tema'): frame.btn_tema.config(text=icone)
        
    def aplicar_tema(self):
        theme = THEMES[self.current_theme]; self.root.configure(bg=theme["bg"])
        for frame in self.frames.values():
            if hasattr(frame, 'recolorir'): frame.recolorir()
            if hasattr(frame, 'recolorir_elementos'): frame.recolorir_elementos()

class TelaSucesso(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.label_sucesso = tk.Label(self, text="✅\n\nLogin bem-sucedido!", font=FONTS["title"]); self.label_sucesso.grid(row=0, column=0)
    def recolorir(self):
        theme = THEMES[self.controller.current_theme]
        self.config(bg=theme['bg']); self.label_sucesso.config(bg=theme['bg'], fg=theme['fg_accent'])

class TelaLogin(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        self.btn_tema = tk.Button(self, font=("Consolas", 14), command=controller.alternar_tema, relief=tk.FLAT, width=3); self.btn_tema.place(relx=0.98, rely=0.03, anchor="ne")
        self.grid_rowconfigure(0, weight=1); self.grid_rowconfigure(1, weight=0); self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)
        self.content_frame = tk.Frame(self); self.content_frame.grid(row=1, column=0, pady=20)
        self.label_titulo = tk.Label(self.content_frame, text="🔑", font=("Consolas", 36)); self.label_titulo.pack(pady=(0, 10))
        self.label_subtitulo = tk.Label(self.content_frame, text="Acesse sua conta", font=FONTS["subtitle"]); self.label_subtitulo.pack(pady=(0, 20))
        self.label_usuario = tk.Label(self.content_frame, text="Usuário:", font=FONTS["subtitle"]); self.label_usuario.pack(pady=(10,0))
        self.entry_usuario = tk.Entry(self.content_frame, font=FONTS["main"], relief=tk.FLAT, width=35, justify='center'); self.entry_usuario.pack(pady=5, padx=50, ipady=4)
        self.label_senha = tk.Label(self.content_frame, text="Senha:", font=FONTS["subtitle"]); self.label_senha.pack(pady=(10,0))
        self.entry_senha = tk.Entry(self.content_frame, show="*", font=FONTS["main"], relief=tk.FLAT, width=35, justify='center'); self.entry_senha.pack(pady=5, padx=50, ipady=4)
        self.btn_entrar = tk.Button(self.content_frame, text="Entrar", command=self.verificar_login, font=FONTS["main"], relief=tk.FLAT, width=15, height=2); self.btn_entrar.pack(pady=20)
        self.btn_cadastrar = tk.Button(self.content_frame, text="Criar Conta", command=lambda: controller.mostrar_tela('TelaCadastro'), font=FONTS["main"], relief=tk.FLAT, width=15); self.btn_cadastrar.pack()

    def recolorir(self):
        theme = THEMES[self.controller.current_theme]; self.config(bg=theme['bg']); self.content_frame.config(bg=theme['bg'])
        for widget in [self.label_titulo, self.label_subtitulo, self.label_usuario, self.label_senha]: widget.config(bg=theme['bg'], fg=theme['fg'])
        for widget in [self.entry_usuario, self.entry_senha]: widget.config(bg=theme['bg_secondary'], fg=theme['fg_accent'], insertbackground=theme['fg'])
        self.btn_entrar.config(bg=theme["btn_cta_bg"], fg=theme["btn_cta_fg"]); self.btn_cadastrar.config(bg=theme["btn_secondary_bg"], fg=theme["btn_secondary_fg"])
        if hasattr(self, 'btn_tema'): self.btn_tema.config(bg=theme["bg"], fg=theme["fg"], activebackground=theme['bg_secondary'], activeforeground=theme['fg'])

    def verificar_login(self):
        usuario = self.entry_usuario.get().strip(); senha = self.entry_senha.get().strip(); senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        cursor = self.controller.db_conn.cursor(); cursor.execute("SELECT senha_hash FROM usuarios WHERE usuario = ?", (usuario,)); resultado = cursor.fetchone()
        if resultado and resultado[0] == senha_hash:
            # <--- ALTERAÇÃO: Chamando as telas pelo nome (string) ---
            self.controller.mostrar_tela('TelaSucesso')
            self.controller.root.after(1000, lambda: self.controller.mostrar_tela('TelaChat'))
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.")

class TelaCadastro(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        self.btn_tema = tk.Button(self, font=("Consolas", 14), command=controller.alternar_tema, relief=tk.FLAT, width=3); self.btn_tema.place(relx=0.98, rely=0.03, anchor="ne")
        self.grid_rowconfigure(0, weight=1); self.grid_rowconfigure(1, weight=0); self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)
        self.content_frame = tk.Frame(self); self.content_frame.grid(row=1, column=0, pady=20)
        self.label_titulo = tk.Label(self.content_frame, text="➕", font=("Consolas", 36)); self.label_titulo.pack(pady=(0, 10))
        self.label_subtitulo = tk.Label(self.content_frame, text="Crie uma nova conta", font=FONTS["subtitle"]); self.label_subtitulo.pack(pady=(0, 20))
        self.label_usuario = tk.Label(self.content_frame, text="Novo usuário:", font=FONTS["subtitle"]); self.label_usuario.pack(pady=(10,0))
        self.entry_novo_usuario = tk.Entry(self.content_frame, font=FONTS["main"], relief=tk.FLAT, width=35, justify='center'); self.entry_novo_usuario.pack(pady=5, padx=50, ipady=4)
        self.label_senha = tk.Label(self.content_frame, text="Senha:", font=FONTS["subtitle"]); self.label_senha.pack(pady=(10,0))
        self.entry_nova_senha = tk.Entry(self.content_frame, show="*", font=FONTS["main"], relief=tk.FLAT, width=35, justify='center'); self.entry_nova_senha.pack(pady=5, padx=50, ipady=4)
        self.btn_cadastrar = tk.Button(self.content_frame, text="Cadastrar", command=self.cadastrar_usuario, font=FONTS["main"], relief=tk.FLAT, width=15, height=2); self.btn_cadastrar.pack(pady=20)
        self.btn_voltar = tk.Button(self.content_frame, text="Voltar para Login", command=lambda: controller.mostrar_tela('TelaLogin'), font=FONTS["main"], relief=tk.FLAT, width=15); self.btn_voltar.pack()

    def recolorir(self):
        theme = THEMES[self.controller.current_theme]
        self.config(bg=theme['bg']); self.content_frame.config(bg=theme['bg'])
        for widget in [self.label_titulo, self.label_subtitulo, self.label_usuario, self.label_senha]: widget.config(bg=theme['bg'], fg=theme['fg'])
        for widget in [self.entry_novo_usuario, self.entry_nova_senha]: widget.config(bg=theme['bg_secondary'], fg=theme['fg_accent'], insertbackground=theme['fg'])
        self.btn_cadastrar.config(bg=theme["btn_primary_bg"], fg=theme["btn_primary_fg"]); self.btn_voltar.config(bg=theme["btn_secondary_bg"], fg=theme["btn_secondary_fg"])
        if hasattr(self, 'btn_tema'): self.btn_tema.config(bg=theme["bg"], fg=theme["fg"], activebackground=theme['bg_secondary'], activeforeground=theme['fg'])
            
    def cadastrar_usuario(self):
        usuario = self.entry_novo_usuario.get().strip(); senha = self.entry_nova_senha.get().strip()
        if not usuario or not senha: messagebox.showerror("Erro", "Preencha todos os campos!"); return
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        try:
            cursor = self.controller.db_conn.cursor(); cursor.execute("INSERT INTO usuarios (usuario, senha_hash) VALUES (?, ?)", (usuario, senha_hash)); self.controller.db_conn.commit()
            messagebox.showinfo("Sucesso", "Usuário cadastrado! Faça o login."); self.controller.mostrar_tela('TelaLogin')
        except sqlite3.IntegrityError: messagebox.showerror("Erro", "Este nome de usuário já existe.")
        except Exception as e: messagebox.showerror("Erro de Banco de Dados", f"Ocorreu um erro: {e}")

class TelaChat(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        frame_topo = tk.Frame(self); frame_topo.pack(fill="x", padx=20, pady=(10,0))
        self.label_titulo = tk.Label(frame_topo, text="💬 Chat de Recomendação", font=FONTS["title"]); self.label_titulo.pack(side="left", expand=True)
        self.btn_tema = tk.Button(frame_topo, font=("Consolas", 14), command=controller.alternar_tema, relief=tk.FLAT, width=3); self.btn_tema.pack(side="right")
        frame_conversa = tk.Frame(self, relief=tk.SUNKEN, bd=0); frame_conversa.pack(padx=20, pady=10, fill="both", expand=True)
        self.texto_conversa = scrolledtext.ScrolledText(frame_conversa, font=FONTS["main"], wrap=tk.WORD, relief=tk.FLAT, bd=10); self.texto_conversa.pack(fill="both", expand=True)
        self.texto_conversa.tag_config("game_title", font=FONTS["main_bold"])
        self.adicionar_mensagem("Olá! Sou seu assistente de recomendação de jogos.", "bot"); self.texto_conversa.config(state=tk.DISABLED)
        frame_entrada = tk.Frame(self); frame_entrada.pack(pady=10, padx=20, fill="x")
        self.placeholder_text = "Digite sua mensagem..."
        self.entrada_mensagem = tk.Entry(frame_entrada, font=FONTS["main"], relief=tk.FLAT); self.entrada_mensagem.pack(side="left", fill="x", expand=True, ipady=8, ipadx=5)
        self.entrada_mensagem.bind("<Return>", self.enviar_mensagem); self.entrada_mensagem.bind("<FocusIn>", self.on_entry_focus_in); self.entrada_mensagem.bind("<FocusOut>", self.on_entry_focus_out); self.on_entry_focus_out(None)
        self.btn_enviar = tk.Button(frame_entrada, text="Enviar", command=self.enviar_mensagem, font=FONTS["main"], relief=tk.FLAT, width=10, height=2); self.btn_enviar.pack(side="left", padx=5)
        self.btn_saindo = tk.Button(self, text="Logout", command=lambda: controller.mostrar_tela('TelaLogin'), font=FONTS["main"], relief=tk.FLAT); self.btn_saindo.pack(pady=5)
        self.is_thinking = False; self.recolorir_elementos()

    def on_entry_focus_in(self, event):
        if self.entrada_mensagem.get() == self.placeholder_text:
            self.entrada_mensagem.delete(0, "end"); self.entrada_mensagem.config(fg=THEMES[self.controller.current_theme]['fg_accent'])

    def on_entry_focus_out(self, event):
        if not self.entrada_mensagem.get():
            self.entrada_mensagem.insert(0, self.placeholder_text); self.entrada_mensagem.config(fg='grey')

    def recolorir_elementos(self):
        theme = THEMES[self.controller.current_theme]
        self.texto_conversa.tag_config("game_title", foreground=theme["game_title"])
        self.config(bg=theme["bg"]); self.label_titulo.config(bg=theme["bg"], fg=theme["fg"]); self.btn_tema.config(bg=theme["bg"], fg=theme["fg"], activebackground=theme['bg_secondary'], activeforeground=theme['fg']); self.texto_conversa.config(bg=theme["bg_secondary"], fg=theme["fg_accent"]); self.texto_conversa.tag_config("usuario", foreground=theme["fg"]); self.texto_conversa.tag_config("bot", foreground=theme["fg_accent"]); self.texto_conversa.tag_config("bot_status", foreground=theme['btn_cta_bg']); self.btn_enviar.config(bg=theme["btn_cta_bg"], fg=theme["btn_cta_fg"]); self.btn_saindo.config(bg=theme["btn_secondary_bg"], fg=theme["btn_secondary_fg"]); self.entrada_mensagem.config(bg=theme["bg_secondary"], insertbackground=theme["fg"])
        self.on_entry_focus_out(None)
        tk.Frame.config(self.winfo_children()[0],bg=theme["bg"]); tk.Frame.config(self.winfo_children()[2],bg=theme["bg"]) 

    def adicionar_mensagem(self, msg, tag):
        self.texto_conversa.config(state=tk.NORMAL); prefixo = "Bot" if tag in ("bot", "bot_status") else "Você"; self.texto_conversa.insert(tk.END, f"{prefixo}: ")
        if tag == "bot" and "**" in msg:
            partes = msg.split('**')
            for i, parte in enumerate(partes):
                if i % 2 == 1: self.texto_conversa.insert(tk.END, parte, "game_title")
                else: self.texto_conversa.insert(tk.END, parte, tag)
        else:
            self.texto_conversa.insert(tk.END, msg, tag)
        self.texto_conversa.insert(tk.END, "\n\n"); self.texto_conversa.config(state=tk.DISABLED); self.texto_conversa.see(tk.END)
    
    def animate_thinking(self, char_index=0):
        if not self.is_thinking: return
        chars = "|/-\\"; line_content = f"Bot: Pesquisando {chars[char_index]}..."
        self.texto_conversa.config(state=tk.NORMAL)
        self.texto_conversa.delete("end-2l linestart", "end-2l lineend")
        self.texto_conversa.insert("end-2l linestart", line_content, "bot_status")
        self.texto_conversa.config(state=tk.DISABLED)
        self.controller.root.after(150, self.animate_thinking, (char_index + 1) % len(chars))

    def enviar_mensagem(self, event=None):
        msg_usuario = self.entrada_mensagem.get().strip()
        if not msg_usuario or msg_usuario == self.placeholder_text: return
        self.adicionar_mensagem(msg_usuario, "usuario"); self.entrada_mensagem.delete(0, "end"); self.on_entry_focus_out(None)
        self.is_thinking = True; self.adicionar_mensagem("Pesquisando...", "bot_status"); self.animate_thinking()
        thread = threading.Thread(target=self.processar_em_background, args=(msg_usuario,)); thread.daemon = True; thread.start()

    def processar_em_background(self, msg_usuario):
        resultados_busca = services.buscar_na_internet(msg_usuario, tipo_busca="geral")
        if self.controller.modelo_ia is None: self.controller.response_queue.put(("Sistema de IA indisponível.", "bot")); return
        try:
            data_atual = datetime.now().strftime("%d de %B de %Y")
            prompt = f"""Você é um especialista em jogos conciso e experiente. A data de hoje é {data_atual}.

            **Tarefa Principal:** Responda à "Pergunta do Usuário" criando uma recomendação em dois parágrafos, usando **apenas** as informações fornecidas no "Contexto da Busca".

            **Parágrafo 1 - As Recomendações:**
            - Recomende e compare de 2 a 3 jogos do contexto que sejam relevantes para a pergunta.
            - Destaque as principais características ou diferenças entre eles.
            - **Sempre** coloque os nomes dos jogos em negrito (ex: **Nome do Jogo**).

            **Parágrafo 2 - Detalhes Técnicos:**
            - Para cada jogo recomendado, liste as informações encontradas no contexto: **Plataformas**, **Preço** e **Tempo de Jogo**.
            - Se uma informação não for encontrada, escreva "Não encontrado".

            **Regra Crítica:** Não se desculpe por problemas técnicos ou falta de acesso. Responda apenas com os fatos presentes no contexto. Se o contexto for insuficiente, simplesmente afirme que não encontrou a informação solicitada.

            Contexto da Busca: --- {resultados_busca} ---
            Pergunta do Usuário: {msg_usuario}
            """
            resposta = self.controller.modelo_ia.generate_content(prompt)
            self.controller.response_queue.put((resposta.text, "bot"))
        except Exception as e:
            self.controller.response_queue.put((f"Ocorreu um erro ao contatar a IA: {e}", "bot"))