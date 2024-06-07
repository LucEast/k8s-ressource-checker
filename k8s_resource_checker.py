import customtkinter as ctk
from kubernetes import client, config
from kubernetes.client import Configuration
import threading
from tkinter import ttk

# Funktion zur Berechnung der Ressourcen
def calculate_resources():
    kubeconfig_path = kubeconfig_entry.get()
    config.load_kube_config(config_file=kubeconfig_path, context=context_var.get())

    v1 = client.CoreV1Api()
    metrics = client.CustomObjectsApi()
    namespaces = v1.list_namespace().items

    results = []
    for ns in namespaces:
        namespace = ns.metadata.name
        pods = v1.list_namespaced_pod(namespace).items
        cpu = 0
        memory = 0
        for pod in pods:
            pod_metrics = metrics.list_namespaced_custom_object(
                "metrics.k8s.io", "v1beta1", namespace, "pods", field_selector=f"metadata.name={pod.metadata.name}"
            )
            for pod_metric in pod_metrics['items']:
                for container in pod_metric['containers']:
                    cpu_usage = container['usage']['cpu']
                    memory_usage = container['usage']['memory']
                    cpu += int(cpu_usage.rstrip('n')) / 1e6  # Convert from nanocores to millicores
                    memory += int(memory_usage.rstrip('Ki')) / 1e3  # Convert from Ki to Mi
        results.append((namespace, round(cpu), round(memory)))

    for row in tree.get_children():
        tree.delete(row)
    
    for ns, cpu, memory in results:
        tree.insert("", "end", values=(ns, cpu, memory))

# Funktion zum Laden der Kontexte aus der Kubeconfig
def load_contexts():
    kubeconfig_path = kubeconfig_entry.get()
    config.load_kube_config(config_file=kubeconfig_path)
    contexts, active_context = config.list_kube_config_contexts()
    context_names = [context['name'] for context in contexts]
    current_context = active_context['name']

    context_menu.configure(values=context_names)
    context_var.set(current_context)

    calculate_button.configure(state="normal")

# GUI Setup
app = ctk.CTk()
app.title("Kubernetes Resource Checker")
app.geometry("800x600")

# Kubeconfig Path
kubeconfig_label = ctk.CTkLabel(app, text="Kubeconfig Path:")
kubeconfig_label.pack(pady=10)
kubeconfig_entry = ctk.CTkEntry(app, width=400)
kubeconfig_entry.pack(pady=10)

# Context Dropdown
context_var = ctk.StringVar()
context_menu = ctk.CTkComboBox(app, variable=context_var, values=[])
context_menu.pack(pady=10)

# Load Contexts Button
load_button = ctk.CTkButton(app, text="Load Contexts", command=load_contexts)
load_button.pack(pady=10)

# Calculate Button
calculate_button = ctk.CTkButton(app, text="Calculate", state="disabled", command=lambda: threading.Thread(target=calculate_resources).start())
calculate_button.pack(pady=10)

# Result Treeview
columns = ("Namespace", "CPU (m)", "Memory (Mi)")
tree = ttk.Treeview(app, columns=columns, show="headings")
tree.heading("Namespace", text="Namespace", anchor="w")
tree.heading("CPU (m)", text="CPU (m)", anchor="center")
tree.heading("Memory (Mi)", text="Memory (Mi)", anchor="center")

tree.column("Namespace", anchor="w")
tree.column("CPU (m)", anchor="center")
tree.column("Memory (Mi)", anchor="center")

tree.pack(pady=10, fill="both", expand=True)

app.mainloop()