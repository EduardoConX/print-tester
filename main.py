import json
import os
import queue
import threading
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import messagebox, ttk


class PrintBuilderApp:
	def __init__(self, root):
		self.root = root
		self.root.title("Constructor de tickets")
		self.root.geometry("720x600")
		self.root.minsize(600, 500)

		self.operations = []
		self.result_queue = queue.Queue()
		self.editor_widgets = []
		self.bold_enabled = False

		self.server_url = tk.StringVar(
			value=os.environ.get("PRINT_SERVER_URL", "")
		)
		self.text_value = tk.StringVar()
		self.alignment_value = tk.StringVar(value="L")
		self.feed_lines = tk.StringVar(value="1")
		self.status = tk.StringVar(value="Listo")

		self._build_ui()
		self.root.after(100, self._check_result)

	def _build_ui(self):
		main = ttk.Frame(self.root, padding=16)
		main.pack(fill="both", expand=True)
		main.columnconfigure(0, weight=1)
		main.rowconfigure(3, weight=1)

		ttk.Label(
			main, text="Constructor de tickets", font=("Segoe UI", 18, "bold")
		).grid(row=0, column=0, sticky="w", pady=(0, 12))

		connection = ttk.LabelFrame(main, text="Servidor de impresión", padding=10)
		connection.grid(row=1, column=0, sticky="ew", pady=(0, 12))
		connection.columnconfigure(1, weight=1)
		ttk.Label(connection, text="URL del endpoint:").grid(
			row=0, column=0, sticky="w", padx=(0, 8)
		)
		url_entry = ttk.Entry(connection, textvariable=self.server_url)
		url_entry.grid(row=0, column=1, sticky="ew")
		self.editor_widgets.append(url_entry)

		controls = ttk.LabelFrame(main, text="Agregar operaciones", padding=10)
		controls.grid(row=2, column=0, sticky="ew", pady=(0, 12))
		controls.columnconfigure(0, weight=1)

		text_row = ttk.Frame(controls)
		text_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
		text_row.columnconfigure(0, weight=1)
		text_entry = ttk.Entry(text_row, textvariable=self.text_value)
		text_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
		text_entry.bind("<Return>", lambda _event: self.add_text())
		self.editor_widgets.append(text_entry)
		self._add_editor_button(
			text_row, "Agregar texto", self.add_text
		).grid(row=0, column=1)

		actions = ttk.Frame(controls)
		actions.grid(row=1, column=0, sticky="w")
		self._add_editor_button(
			actions, "Salto de línea", self.add_line_break
		).pack(side="left", padx=(0, 6))

		ttk.Label(actions, text="Alinear:").pack(side="left", padx=(4, 4))
		alignment = ttk.Combobox(
			actions,
			textvariable=self.alignment_value,
			values=("L", "C", "R"),
			state="readonly",
			width=4,
		)
		alignment.pack(side="left", padx=(0, 4))
		self.editor_widgets.append(alignment)
		self._add_editor_button(
			actions, "Agregar alineación", self.add_alignment
		).pack(side="left", padx=(0, 6))

		self.bold_button = self._add_editor_button(
			actions, "Negrita: OFF", self.toggle_bold
		)
		self.bold_button.pack(side="left", padx=(0, 6))
		self._add_editor_button(
			actions, "Alimentar papel", self.add_feed
		).pack(side="left", padx=(0, 4))
		self.feed_lines_box = ttk.Spinbox(
			actions, from_=1, to=255, textvariable=self.feed_lines, width=5
		)
		self.feed_lines_box.pack(side="left")
		self.editor_widgets.append(self.feed_lines_box)

		preview_frame = ttk.LabelFrame(main, text="Vista previa de operaciones", padding=10)
		preview_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 12))
		preview_frame.columnconfigure(0, weight=1)
		preview_frame.rowconfigure(0, weight=1)

		self.preview = tk.Listbox(preview_frame, activestyle="dotbox", height=10)
		self.preview.grid(row=0, column=0, sticky="nsew")
		scrollbar = ttk.Scrollbar(
			preview_frame, orient="vertical", command=self.preview.yview
		)
		scrollbar.grid(row=0, column=1, sticky="ns")
		self.preview.configure(yscrollcommand=scrollbar.set)

		preview_actions = ttk.Frame(preview_frame)
		preview_actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
		self.remove_button = ttk.Button(
			preview_actions, text="Quitar seleccionada", command=self.remove_selected
		)
		self.remove_button.pack(side="left")
		self.clear_button = ttk.Button(
			preview_actions, text="Vaciar ticket", command=self.clear_operations
		)
		self.clear_button.pack(side="left", padx=(6, 0))
		self.editor_widgets.extend((self.remove_button, self.clear_button))

		footer = ttk.Frame(main)
		footer.grid(row=4, column=0, sticky="ew")
		footer.columnconfigure(0, weight=1)
		ttk.Label(footer, textvariable=self.status).grid(row=0, column=0, sticky="w")
		self.print_button = ttk.Button(
			footer, text="Imprimir", command=self.print_ticket
		)
		self.print_button.grid(row=0, column=1, sticky="e")

	def _add_editor_button(self, parent, text, command):
		button = ttk.Button(parent, text=text, command=command)
		self.editor_widgets.append(button)
		return button

	def _add_operation(self, action, data):
		self.operations.append({"action": action, "data": data})
		self._refresh_preview()

	def add_text(self):
		self._add_operation("text", self.text_value.get())
		self.text_value.set("")

	def add_line_break(self):
		self._add_operation("enter", "")

	def add_alignment(self):
		self._add_operation("alignment", self.alignment_value.get())

	def toggle_bold(self):
		self.bold_enabled = not self.bold_enabled
		value = "1" if self.bold_enabled else "0"
		self.bold_button.configure(
			text=f"Negrita: {'ON' if self.bold_enabled else 'OFF'}"
		)
		self._add_operation("boldText", value)

	def add_feed(self):
		try:
			lines = int(self.feed_lines.get())
		except ValueError:
			messagebox.showerror("Valor no válido", "Las líneas deben ser un número.")
			return

		if not 1 <= lines <= 255:
			messagebox.showerror(
				"Valor no válido", "El número de líneas debe estar entre 1 y 255."
			)
			return

		self._add_operation("feed", str(lines))

	def remove_selected(self):
		selected = self.preview.curselection()
		if selected:
			del self.operations[selected[0]]
			self._refresh_preview()

	def clear_operations(self):
		self.operations.clear()
		self.bold_enabled = False
		self.bold_button.configure(text="Negrita: OFF")
		self._refresh_preview()

	def _refresh_preview(self):
		labels = {
			"text": "Texto",
			"enter": "Salto de línea",
			"alignment": "Alinear",
			"boldText": "Negrita",
			"feed": "Alimentar papel",
		}
		self.preview.delete(0, tk.END)
		for operation in self.operations:
			action = operation["action"]
			data = operation["data"]
			display_data = repr(data) if action == "text" else data
			self.preview.insert(
				tk.END, f"{labels[action]}: {display_data}"
			)

	def print_ticket(self):
		url = self.server_url.get().strip()
		if not url:
			messagebox.showerror(
				"Falta la URL", "Introduce la URL del servidor de impresión."
			)
			return
		if not self.operations:
			messagebox.showerror("Ticket vacío", "Agrega al menos una operación.")
			return

		payload = json.dumps({"operations": self.operations}).encode("utf-8")
		batch = [operation.copy() for operation in self.operations]
		request = urllib.request.Request(
			url,
			data=payload,
			headers={"Content-Type": "application/json"},
			method="POST",
		)

		self._set_editing_enabled(False)
		self.print_button.configure(state="disabled")
		self.status.set("Enviando al servidor...")
		threading.Thread(
			target=self._send_request, args=(request, batch), daemon=True
		).start()

	def _send_request(self, request, batch):
		try:
			with urllib.request.urlopen(request, timeout=15) as response:
				result = json.loads(response.read().decode("utf-8"))
			if result.get("status") != "ok":
				raise RuntimeError(
					result.get("error", "El servidor no confirmó la impresión.")
				)
			self.result_queue.put((True, "Impresión confirmada.", batch))
		except urllib.error.HTTPError as error:
			self.result_queue.put(
				(False, f"El servidor respondió HTTP {error.code}.", batch)
			)
		except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
			self.result_queue.put((False, f"No se pudo imprimir: {error}", batch))
		except Exception as error:
			self.result_queue.put((False, str(error), batch))

	def _check_result(self):
		try:
			success, message, batch = self.result_queue.get_nowait()
		except queue.Empty:
			pass
		else:
			self._set_editing_enabled(True)
			self.print_button.configure(state="normal")
			self.status.set(message)
			if success:
				if self.operations[: len(batch)] == batch:
					del self.operations[: len(batch)]
				self._refresh_preview()
				self.bold_enabled = False
				self.bold_button.configure(text="Negrita: OFF")
			else:
				messagebox.showerror("Error de impresión", message)

		self.root.after(100, self._check_result)

	def _set_editing_enabled(self, enabled):
		state = "!disabled" if enabled else "disabled"
		for widget in self.editor_widgets:
			widget.state([state])


if __name__ == "__main__":
	ventana = tk.Tk()
	PrintBuilderApp(ventana)
	ventana.mainloop()
