import os

def ver_tripas_vscode():
    print("--- DIAGNÓSTICO DE EXTENSIONES VS CODE ---")
    
    # Ruta estándar
    user_profile = os.environ.get('USERPROFILE')
    extensions_path = os.path.join(user_profile, '.vscode', 'extensions')
    
    print(f"Buscando en: {extensions_path}")
    
    if os.path.exists(extensions_path):
        carpetas = os.listdir(extensions_path)
        print(f"Total carpetas encontradas: {len(carpetas)}")
        print("-" * 30)
        
        # Filtramos solo las que parecen de IA para no llenar la pantalla
        sospechosas = []
        for c in carpetas:
            lower_c = c.lower()
            if any(x in lower_c for x in ['copilot', 'chat', 'gpt', 'ai', 'blackbox', 'tabnine']):
                print(f"[SOSPECHOSA] -> {c}")
                sospechosas.append(c)
            else:
                # Imprimimos algunas normales solo para ver que funciona
                pass
        
        if not sospechosas:
            print("EXTRAÑO: No se encontraron carpetas con nombres de IA.")
            print("Listando TODAS las carpetas (primeras 10):")
            for c in carpetas[:10]:
                print(f" - {c}")
    else:
        print("ERROR CRÍTICO: No existe la carpeta .vscode/extensions")

if __name__ == "__main__":
    ver_tripas_vscode()