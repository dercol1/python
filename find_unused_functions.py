#!/usr/bin/env python3

# Miglioramenti Principali
#
#     Supporto per le Classi:
#         Rileva le definizioni di classe
#         Tiene traccia dei metodi definiti all'interno delle classi
#         Gestisce correttamente le chiamate self.method()
#     Statistiche Dettagliate:
#         Mostra il numero di chiamate per ogni funzione
#         Mostra il numero di chiamate per ogni metodo di classe
#         Organizza le statistiche per classe
#     Report Strutturato:
#         Sezione dedicata alle classi e ai loro metodi
#         Sezione per le funzioni globali
#         Sezione per elementi non utilizzati



import ast
import os
from pathlib import Path
from collections import defaultdict

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.defined_functions = {}  # {name: (lineno, end_lineno)}
        self.defined_methods = defaultdict(dict)  # {class_name: {method_name: (lineno, end_lineno)}}
        self.defined_classes = {}  # {name: (lineno, end_lineno)}

        self.function_calls = defaultdict(list)  # {name: [line_numbers]}
        self.method_calls = defaultdict(lambda: defaultdict(list))  # {class_name: {method_name: [line_numbers]}}

        self.current_class = None
        self.class_methods = defaultdict(set)

    def visit_ClassDef(self, node):
        self.defined_classes[node.name] = (node.lineno, node.end_lineno)
        previous_class = self.current_class
        self.current_class = node.name
        # Memorizza tutti i metodi della classe
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.class_methods[node.name].add(item.name)
        self.generic_visit(node)
        self.current_class = previous_class

    def visit_FunctionDef(self, node):
        if self.current_class:
            self.defined_methods[self.current_class][node.name] = (node.lineno, node.end_lineno)
        else:
            self.defined_functions[node.name] = (node.lineno, node.end_lineno)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            # Chiamata diretta di funzione
            self.function_calls[node.func.id].append(node.lineno)
        elif isinstance(node.func, ast.Attribute):
            # Gestione chiamate tipo obj.method()
            method_name = node.func.attr

            # Cerca il metodo in tutte le classi definite
            for class_name, methods in self.class_methods.items():
                if method_name in methods:
                    self.method_calls[class_name][method_name].append(node.lineno)

        self.generic_visit(node)


def analyze_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        tree = ast.parse(content)
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)

        print(f"\n=== Analisi del file: {file_path} ===")

        # Statistiche delle classi e metodi
        if analyzer.defined_classes:
            print("\n#### Classi definite:")
            for class_name, (class_start, class_end) in analyzer.defined_classes.items():
                print(f"\nClasse: {class_name} (linee {class_start}-{class_end})")
                if class_name in analyzer.defined_methods:
                    print("  Metodi:")
                    for method, (m_start, m_end) in analyzer.defined_methods[class_name].items():
                        calls = analyzer.method_calls[class_name][method]
                        print(f"    - {method} (linee {m_start}-{m_end}):")
                        print(f"      Chiamate: {len(calls)} volte")
                        if calls:
                            print(f"      Linee di chiamata: {sorted(calls)}")

        # Statistiche delle funzioni
        if analyzer.defined_functions:
            print("\n#### Funzioni globali:")
            for func, (f_start, f_end) in analyzer.defined_functions.items():
                calls = analyzer.function_calls[func]
                print(f"- {func} (linee {f_start}-{f_end}):")
                print(f"  Chiamate: {len(calls)} volte")
                if calls:
                    print(f"  Linee di chiamata: {sorted(calls)}")

        # Metodi non utilizzati
        print("\n#### Metodi non utilizzati per classe:")
        for class_name in analyzer.defined_classes:
            unused_methods = {m: pos for m, pos in analyzer.defined_methods[class_name].items()
                            if not analyzer.method_calls[class_name][m] and m != '__init__'}
            if unused_methods:
                print(f"\nClasse {class_name}:")
                for method, (start, end) in unused_methods.items():
                    print(f"- {method} (linee {start}-{end})")

    except Exception as e:
        print(f"Errore nell'analisi di {file_path}: {str(e)}")



def main(path):
    target = Path(path)

    if target.is_file() and target.suffix == '.py':
        analyze_file(target)
    elif target.is_dir():
        for python_file in target.glob('**/*.py'):
            analyze_file(python_file)
    else:
        print("Il percorso specificato non è valido o non è un file/cartella Python")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Specificare un file o una cartella da analizzare")
